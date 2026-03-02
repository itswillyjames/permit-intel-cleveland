"""
Municipal Intelligence - Permit Intel Cleveland
Enterprise-grade permit ingestion & scoring system

Architecture:
- Robust ArcGIS schema detection (no hard-coded field names)
- Automatic layer discovery with validation
- In-memory caching with TTL
- Structured logging for debugging
- Defensive scoring engine
- Free-tier only (ArcGIS public, no paid APIs)
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from flask import Flask, jsonify, render_template

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", template_folder="templates")

# ============================================================================
# ARCGIS CONFIGURATION & CONSTANTS
# ============================================================================

ARCGIS_FEATURE_SERVER = (
    "https://services2.arcgis.com/CyVvlIiUfRBmMQuu/arcgis/rest/services/"
    "Building_Permits_Applications_view/FeatureServer"
)

# Request configuration
ARCGIS_TIMEOUT = 30
ARCGIS_MAX_RETRIES = 3
ARCGIS_RETRY_DELAY = 1

# Cache configuration
CACHE_TTL_SECONDS = 300  # 5 minutes
MAX_PERMITS_PER_QUERY = 100

# ============================================================================
# CACHE IMPLEMENTATION
# ============================================================================

class CacheEntry:
    """Simple cache entry with TTL"""
    def __init__(self, data: Any, ttl_seconds: int):
        self.data = data
        self.created_at = datetime.now()
        self.ttl = ttl_seconds
    
    def is_valid(self) -> bool:
        """Check if cache entry has expired"""
        age = (datetime.now() - self.created_at).total_seconds()
        return age < self.ttl


class SimpleCache:
    """In-memory cache with TTL support"""
    def __init__(self):
        self.cache: Dict[str, CacheEntry] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if valid"""
        if key in self.cache:
            entry = self.cache[key]
            if entry.is_valid():
                logger.info(f"Cache hit for key: {key}")
                return entry.data
            else:
                logger.info(f"Cache expired for key: {key}")
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = CACHE_TTL_SECONDS):
        """Set value in cache with TTL"""
        self.cache[key] = CacheEntry(value, ttl_seconds)
        logger.info(f"Cache set for key: {key} (TTL: {ttl_seconds}s)")
    
    def clear(self):
        """Clear entire cache"""
        self.cache.clear()
        logger.info("Cache cleared")


cache = SimpleCache()

# ============================================================================
# ARCGIS LAYER DETECTION & SCHEMA DISCOVERY
# ============================================================================

class ArcGISSchemaDetector:
    """
    Automatically detects correct layer and discovers field schema.
    Logs all discoveries for debugging.
    """
    
    def __init__(self, feature_server_url: str):
        self.feature_server_url = feature_server_url
        self.detected_layer_id: Optional[int] = None
        self.discovered_fields: Dict[str, Dict[str, Any]] = {}
    
    def discover_layers(self) -> List[int]:
        """
        Get list of available layer IDs from FeatureServer.
        
        Returns:
            List of layer IDs (empty list if none found)
        """
        try:
            logger.info(f"Discovering layers from {self.feature_server_url}...")
            
            response = requests.get(
                f"{self.feature_server_url}?f=json",
                timeout=ARCGIS_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                logger.error(f"ArcGIS API error: {data['error']}")
                return []
            
            layers = [layer.get("id") for layer in data.get("layers", [])]
            logger.info(f"Discovered {len(layers)} layers: {layers}")
            
            return layers
        
        except requests.RequestException as e:
            logger.error(f"Network error discovering layers: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error discovering layers: {e}")
            return []
    
    def get_layer_schema(self, layer_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Get field schema for a specific layer.
        
        Returns:
            Dict mapping field names to metadata (type, nullable, etc.)
        """
        try:
            logger.info(f"Fetching schema for layer {layer_id}...")
            
            response = requests.get(
                f"{self.feature_server_url}/{layer_id}?f=json",
                timeout=ARCGIS_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                logger.error(f"ArcGIS API error for layer {layer_id}: {data['error']}")
                return {}
            
            fields = {}
            for field in data.get("fields", []):
                field_name = field.get("name")
                if field_name:
                    fields[field_name] = {
                        "type": field.get("type"),
                        "nullable": field.get("nullable", True),
                        "length": field.get("length")
                    }
            
            logger.info(f"Layer {layer_id} has {len(fields)} fields: {list(fields.keys())}")
            self.discovered_fields[layer_id] = fields
            
            return fields
        
        except requests.RequestException as e:
            logger.error(f"Network error fetching schema for layer {layer_id}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching schema for layer {layer_id}: {e}")
            return {}
    
    def test_layer_has_data(self, layer_id: int) -> bool:
        """
        Test if a layer actually has records.
        
        Returns:
            True if layer has at least 1 record
        """
        try:
            logger.info(f"Testing layer {layer_id} for data...")
            
            response = requests.get(
                f"{self.feature_server_url}/{layer_id}/query",
                params={
                    "f": "json",
                    "where": "1=1",
                    "returnCountOnly": "true",
                    "resultRecordCount": "1"
                },
                timeout=ARCGIS_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                logger.warning(f"Layer {layer_id} returned error: {data['error']}")
                return False
            
            count = data.get("count", 0)
            logger.info(f"Layer {layer_id} has {count} records")
            
            return count > 0
        
        except Exception as e:
            logger.error(f"Error testing layer {layer_id}: {e}")
            return False
    
    def find_permit_layer(self) -> Optional[int]:
        """
        Automatically find the correct layer ID containing permit data.
        
        ArcGIS commonly returns 0 layers in the FeatureServer endpoint but
        still has Layer 0 available. We test common layer IDs.
        
        Returns:
            Layer ID if found, None otherwise
        """
        logger.info("Starting automatic layer detection...")
        
        layers = self.discover_layers()
        
        # If no layers discovered, try common layer IDs (0 is default)
        if not layers:
            logger.info("No layers in discovery response, trying common layer IDs...")
            layers = [0]  # Most common default
        
        for layer_id in layers:
            logger.info(f"Evaluating layer {layer_id}...")
            
            # Check if layer has data
            if not self.test_layer_has_data(layer_id):
                logger.warning(f"Layer {layer_id} has no data, skipping")
                continue
            
            # Get schema to make sure it's permit-like
            schema = self.get_layer_schema(layer_id)
            if not schema:
                logger.warning(f"Layer {layer_id} has no schema, skipping")
                continue
            
            # Look for permit-like fields
            field_names_lower = {name.lower(): name for name in schema.keys()}
            
            has_permit_fields = any(
                keyword in field_names_lower
                for keyword in ["permit", "application", "status", "address"]
            )
            
            if has_permit_fields:
                logger.info(f"✓ Layer {layer_id} appears to be a permit layer")
                self.detected_layer_id = layer_id
                return layer_id
            
            logger.warning(f"Layer {layer_id} doesn't look like a permit layer")
        
        logger.error("No suitable permit layer found")
        return None


# ============================================================================
# ARCGIS DATA FETCHER WITH ROBUST ERROR HANDLING
# ============================================================================

class PermitFetcher:
    """
    Fetches permits from ArcGIS with automatic retry, timeout,
    and dynamic field mapping.
    """
    
    def __init__(self, feature_server_url: str, layer_id: int):
        self.feature_server_url = feature_server_url
        self.layer_id = layer_id
        self.schema_detector = ArcGISSchemaDetector(feature_server_url)
        self.available_fields: Dict[str, str] = {}
        self._discover_available_fields()
    
    def _discover_available_fields(self):
        """
        Discover what fields are available and map them to standard names.
        This avoids hardcoding field names.
        """
        schema = self.schema_detector.get_layer_schema(self.layer_id)
        field_names_lower = {name.lower(): name for name in schema.keys()}
        
        # Map to standard fields - use what exists
        self.available_fields = {}
        
        # Permit ID (try multiple variations)
        for candidate in ["permitnumber", "permit_number", "applicationid", "application_id", "objectid"]:
            if candidate in field_names_lower:
                self.available_fields["permit_id"] = field_names_lower[candidate]
                logger.info(f"Mapped permit_id to {field_names_lower[candidate]}")
                break
        
        # Address
        for candidate in ["streetaddress", "street_address", "address", "propertyaddress", "property_address"]:
            if candidate in field_names_lower:
                self.available_fields["address"] = field_names_lower[candidate]
                logger.info(f"Mapped address to {field_names_lower[candidate]}")
                break
        
        # Status
        for candidate in ["status", "permit_status", "applicationstatus", "application_status"]:
            if candidate in field_names_lower:
                self.available_fields["status"] = field_names_lower[candidate]
                logger.info(f"Mapped status to {field_names_lower[candidate]}")
                break
        
        # Description/scope of work
        for candidate in ["workdesc", "work_desc", "projectdescription", "project_description", 
                         "scopeofwork", "scope_of_work", "description"]:
            if candidate in field_names_lower:
                self.available_fields["description"] = field_names_lower[candidate]
                logger.info(f"Mapped description to {field_names_lower[candidate]}")
                break
        
        # Estimated value/cost
        for candidate in ["estimatedcost", "estimated_cost", "projectvalue", "project_value", 
                         "jobcost", "job_cost", "valuation", "value", "cost"]:
            if candidate in field_names_lower:
                self.available_fields["value"] = field_names_lower[candidate]
                logger.info(f"Mapped value to {field_names_lower[candidate]}")
                break
        
        # Owner/applicant name (try multiple variations)
        for candidate in ["ownername", "owner_name", "applicantname", "applicant_name", 
                         "contractorname", "contractor_name", "createdby", "created_by",
                         "permittype", "permit_type", "constructiontype", "construction_type"]:
            if candidate in field_names_lower:
                self.available_fields["owner"] = field_names_lower[candidate]
                logger.info(f"Mapped owner to {field_names_lower[candidate]}")
                break
        
        logger.info(f"Final field mapping: {self.available_fields}")
    
    def fetch_permits(self, limit: int = MAX_PERMITS_PER_QUERY) -> List[Dict[str, Any]]:
        """
        Fetch permits with retry logic and comprehensive error handling.
        
        Args:
            limit: Maximum number of permits to return
        
        Returns:
            List of normalized permit records
        """
        # Check cache first
        cache_key = f"permits_{self.layer_id}_{limit}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        logger.info(f"Fetching permits from layer {self.layer_id} (limit: {limit})...")
        
        for attempt in range(ARCGIS_MAX_RETRIES):
            try:
                query_url = f"{self.feature_server_url}/{self.layer_id}/query"
                
                params = {
                    "f": "json",
                    "where": "1=1",
                    "outFields": "*",
                    "returnGeometry": False,
                    "resultRecordCount": str(limit),
                    "maxAllowableOffset": 0
                }
                
                logger.info(f"Query attempt {attempt + 1}/{ARCGIS_MAX_RETRIES}: {query_url}")
                
                response = requests.get(
                    query_url,
                    params=params,
                    timeout=ARCGIS_TIMEOUT
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Log response metadata
                response_size = len(json.dumps(data))
                features_count = len(data.get("features", []))
                logger.info(f"✓ Response size: {response_size} bytes, features: {features_count}")
                
                if "error" in data:
                    logger.error(f"ArcGIS API error: {data['error']}")
                    if attempt < ARCGIS_MAX_RETRIES - 1:
                        logger.info(f"Retrying in {ARCGIS_RETRY_DELAY}s...")
                        __import__('time').sleep(ARCGIS_RETRY_DELAY)
                    continue
                
                # Parse and normalize results
                permits = self._normalize_permits(data.get("features", []))
                
                logger.info(f"Parsed {len(permits)} permits from {features_count} features")
                
                # Cache the result
                cache.set(cache_key, permits, CACHE_TTL_SECONDS)
                
                return permits
            
            except requests.Timeout:
                logger.error(f"Request timeout on attempt {attempt + 1}/{ARCGIS_MAX_RETRIES}")
                if attempt < ARCGIS_MAX_RETRIES - 1:
                    logger.info(f"Retrying in {ARCGIS_RETRY_DELAY}s...")
                    __import__('time').sleep(ARCGIS_RETRY_DELAY)
            
            except requests.RequestException as e:
                logger.error(f"Network error on attempt {attempt + 1}/{ARCGIS_MAX_RETRIES}: {e}")
                if attempt < ARCGIS_MAX_RETRIES - 1:
                    logger.info(f"Retrying in {ARCGIS_RETRY_DELAY}s...")
                    __import__('time').sleep(ARCGIS_RETRY_DELAY)
            
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}/{ARCGIS_MAX_RETRIES}: {e}")
                if attempt < ARCGIS_MAX_RETRIES - 1:
                    logger.info(f"Retrying in {ARCGIS_RETRY_DELAY}s...")
                    __import__('time').sleep(ARCGIS_RETRY_DELAY)
        
        logger.error(f"Failed to fetch permits after {ARCGIS_MAX_RETRIES} attempts")
        return []
    
    def _normalize_permits(self, features: List[Dict]) -> List[Dict[str, Any]]:
        """
        Convert raw ArcGIS features to normalized permit records.
        
        Args:
            features: Raw feature list from ArcGIS
        
        Returns:
            List of normalized permit dicts
        """
        permits = []
        
        for feature in features:
            try:
                attrs = feature.get("attributes", {})
                if not attrs:
                    logger.warning("Feature with no attributes encountered")
                    continue
                
                permit = self._extract_permit_record(attrs)
                permits.append(permit)
            
            except Exception as e:
                logger.error(f"Error normalizing feature: {e}")
                continue
        
        return permits
    
    def _extract_permit_record(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and normalize a single permit record from attributes.
        
        Args:
            attributes: Raw attributes from ArcGIS feature
        
        Returns:
            Normalized permit record
        """
        # Safe getters
        def safe_get(attr_name: str) -> Optional[Any]:
            return attributes.get(self.available_fields.get(attr_name), None)
        
        def safe_string(value: Any) -> str:
            if value is None:
                return ""
            return str(value).strip()
        
        def safe_float(value: Any) -> float:
            if value is None:
                return 0.0
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0
        
        # Extract fields
        permit_id = safe_string(safe_get("permit_id"))
        address = safe_string(safe_get("address"))
        status = safe_string(safe_get("status"))
        description = safe_string(safe_get("description"))
        value = safe_float(safe_get("value"))
        owner = safe_string(safe_get("owner"))
        
        # Build normalized permit record
        permit = {
            "permit_id": permit_id or "UNKNOWN",
            "address": address or "No address provided",
            "status": status or "Unknown",
            "description": description or "No description",
            "value": max(0.0, value),  # Ensure non-negative
            "owner": owner or "Unknown",
        }
        
        # Calculate score and deal type
        permit["score"] = score_permit(permit)
        permit["deal_type"] = classify_deal_type(permit)
        
        return permit


# ============================================================================
# SCORING ENGINE
# ============================================================================

def score_permit(permit: Dict[str, Any]) -> int:
    """
    Production-grade scoring engine.
    Returns integer score 0-100 based on permit characteristics.
    
    Scoring tiers:
    - Value: High-value permits (40 pts)
    - Status: Urgent/In-Progress (25 pts)
    - Keywords: Commercial/retail/hospitality (15 pts)
    - Owner: LLC/corporate entities (10 pts)
    - Other: Type-based bonuses (10 pts)
    
    Args:
        permit: Normalized permit record
    
    Returns:
        Integer score 0-100
    """
    score = 0
    
    # VALUE TIER (0-40 points)
    value = permit.get("value", 0)
    if value >= 5000000:
        score += 40
    elif value >= 2000000:
        score += 35
    elif value >= 1000000:
        score += 30
    elif value >= 500000:
        score += 25
    elif value >= 250000:
        score += 20
    elif value >= 100000:
        score += 15
    elif value >= 50000:
        score += 10
    elif value > 0:
        score += 5
    
    # STATUS URGENCY DETECTION (0-25 points)
    status_lower = str(permit.get("status", "")).lower()
    
    urgent_keywords = ["under review", "in review", "in progress", "active", 
                       "pending", "submitted", "incomplete"]
    if any(keyword in status_lower for keyword in urgent_keywords):
        score += 25
    elif "issued" in status_lower:
        score += 15
    elif "approved" in status_lower:
        score += 10
    elif "closed" in status_lower or "completed" in status_lower:
        score += 2
    
    # COMMERCIAL KEYWORD DETECTION (0-15 points)
    description_lower = str(permit.get("description", "")).lower()
    owner_lower = str(permit.get("owner", "")).lower()
    full_text = description_lower + " " + owner_lower
    
    commercial_keywords = [
        "commercial", "retail", "restaurant", "bar", "cafe", "hotel", "motel",
        "warehouse", "industrial", "factory", "manufacturing", "office", "apt",
        "apartment", "multi-unit", "condominium", "mixed-use", "shopping",
        "supermarket", "grocery", "mall", "plaza", "center"
    ]
    
    keyword_matches = sum(1 for keyword in commercial_keywords if keyword in full_text)
    score += min(15, keyword_matches * 3)
    
    # MECHANICAL/MAJOR WORK KEYWORDS (0-10 points)
    major_keywords = [
        "hvac", "mechanical", "plumbing", "electrical", "roofing", "foundation",
        "structural", "sprinkler", "fire system", "elevator", "renovation",
        "remodel", "addition", "demolition"
    ]
    
    major_matches = sum(1 for keyword in major_keywords if keyword in description_lower)
    score += min(10, major_matches * 2)
    
    # OWNER LLC/CORPORATE DETECTION (0-10 points)
    if any(entity_type in owner_lower for entity_type in ["llc", "inc", "corp", "co.", "ltd", "pllc"]):
        score += 10
    
    # OWNER NAME REPEATS (0-5 points) - indicates experienced investor
    if len(owner_lower) > 5 and owner_lower.count(" ") >= 1:
        # More complex names suggest established entities
        score += 3
    
    # CAP AT 100
    return min(100, max(0, int(score)))


def classify_deal_type(permit: Dict[str, Any]) -> str:
    """
    Classify permit into deal type categories.
    
    Categories:
    - Premium Development (high value, commercial)
    - Financing + Arbitrage opportunity (high value)
    - Timeline leverage (under review/active)
    - Maintenance/Compliance (low-moderate value)
    - Supplier/GC Arbitrage (moderate value)
    
    Args:
        permit: Normalized permit record
    
    Returns:
        Deal type classification string
    """
    value = permit.get("value", 0)
    status = str(permit.get("status", "")).lower()
    description = str(permit.get("description", "")).lower()
    
    # Premium Development
    if value > 2500000:
        return "Premium Development"
    
    # Financing + Arbitrage
    if value > 1500000:
        return "Financing + Arbitrage"
    
    # Timeline Leverage (active permits)
    if any(keyword in status for keyword in ["review", "progress", "active", "pending"]):
        if value > 250000:
            return "Timeline Leverage"
    
    # Major systems
    major_systems = ["hvac", "plumbing", "electrical", "roofing", "sprinkler"]
    if any(sys in description for sys in major_systems):
        if value > 75000:
            return "Major Systems Opportunity"
    
    # Maintenance/Compliance
    if value < 50000:
        return "Maintenance/Compliance"
    
    # Default
    return "Supplier/GC Arbitrage"


# ============================================================================
# INITIALIZATION & STARTUP
# ============================================================================

def initialize_arcgis():
    """
    Initialize ArcGIS connection and find permit layer.
    Runs once on startup.
    
    Returns:
        Tuple of (detector, fetcher) or (None, None) if failed
    """
    logger.info("="*80)
    logger.info("INITIALIZING ARCGIS PERMIT INTEL")
    logger.info("="*80)
    
    detector = ArcGISSchemaDetector(ARCGIS_FEATURE_SERVER)
    layer_id = detector.find_permit_layer()
    
    if layer_id is None:
        logger.error("FATAL: Could not find permit layer in ArcGIS FeatureServer")
        return None, None
    
    logger.info(f"✓ Found permit layer: {layer_id}")
    
    try:
        fetcher = PermitFetcher(ARCGIS_FEATURE_SERVER, layer_id)
        logger.info("✓ PermitFetcher initialized")
        return detector, fetcher
    except Exception as e:
        logger.error(f"Failed to initialize PermitFetcher: {e}")
        return None, None


# Initialize on startup
detector, fetcher = initialize_arcgis()

if fetcher is None:
    logger.warning("WARNING: No permit fetcher available. API will return empty results.")


# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.get("/")
def home():
    """Render dashboard homepage"""
    return render_template("dashboard.html")


@app.get("/api/permits")
def api_permits():
    """
    API endpoint to fetch permits.
    
    Returns:
        JSON array of permit records, or error response
    """
    if fetcher is None:
        logger.error("API request but no fetcher initialized")
        return jsonify({
            "error": "permit_service_unavailable",
            "message": "Permit ingestion service is not available",
            "permits": []
        }), 503
    
    try:
        permits = fetcher.fetch_permits(limit=MAX_PERMITS_PER_QUERY)
        
        logger.info(f"API returning {len(permits)} permits")
        
        return jsonify({
            "success": True,
            "count": len(permits),
            "permits": permits,
            "cached": False,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in API response: {e}")
        return jsonify({
            "error": "internal_error",
            "message": str(e),
            "permits": []
        }), 500


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy" if fetcher else "degraded",
        "permits_available": fetcher is not None,
        "cache_size": len(cache.cache),
        "timestamp": datetime.now().isoformat()
    })


@app.get("/api/clear-cache")
def clear_cache_endpoint():
    """Clear the permit cache (admin endpoint)"""
    cache.clear()
    return jsonify({
        "message": "Cache cleared",
        "timestamp": datetime.now().isoformat()
    })


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "not_found",
        "message": "The requested resource was not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {error}")
    return jsonify({
        "error": "internal_server_error",
        "message": "An internal server error occurred"
    }), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    logger.info(f"Starting Flask app on 0.0.0.0:{port}")
    logger.info(f"Environment: {'production' if os.environ.get('FLASK_ENV') == 'production' else 'development'}")
    app.run(host="0.0.0.0", port=port, debug=False)
