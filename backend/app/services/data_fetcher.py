"""
Data source fetching service - Integrate with Socrata and ArcGIS for real permit data
"""
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Pre-configured free data sources by city
FREE_DATA_SOURCES = {
    "San Francisco": {
        "socrata": "https://data.sfgov.org/resource/i98e-djp9.json",
        "fields": {
            "permit_number": "permit_number",
            "submitted_date": "submitted_date",
            "issued_date": "issued_date",
            "completed_date": "completed_date",
            "description": "description",
            "permit_type": "permit_type",
            "address": "street_number,street_name",
            "valuation": "estimated_cost",
            "status": "status",
            "applicant_first_name": "applicant_first_name",
            "applicant_last_name": "applicant_last_name",
            "contractor_company": "contractor_company"
        }
    },
    "New York": {
        "socrata": "https://data.cityofnewyork.us/resource/wvjb-nzaa.json",
        "fields": {
            "permit_id": "permit_number",
            "submitted_date": "issued_date",
            "issued_date": "issued_date",
            "description": "job_description",
            "permit_type": "permit_type",
            "address": "house_number,street_name",
            "valuation": "estimated_cost",
            "status": "permit_status",
            "applicant": "applicant_name",
            "contractor": "contractor_name"
        }
    },
    "Los Angeles": {
        "socrata": "https://data.lacity.org/resource/y4zb-t59m.json",
        "fields": {
            "permit_id": "permit_number",
            "submitted_date": "permit_filed_date",
            "issued_date": "permit_issued_date",
            "description": "description",
            "permit_type": "permit_type",
            "address": "street_address",
            "valuation": "valuation",
            "status": "permit_status",
            "applicant": "applicant_name",
            "contractor": "contractor"
        }
    },
    "Chicago": {
        "socrata": "https://data.cityofchicago.org/resource/ydr8-5enu.json",
        "fields": {
            "permit_id": "permit_number",
            "submitted_date": "issue_date",
            "issued_date": "issue_date",
            "description": "description",
            "permit_type": "permit_type",
            "address": "street_address",
            "valuation": "estimated_cost",
            "status": "status",
            "applicant": "applicant_name",
            "contractor": "contractor_name"
        }
    }
}


def fetch_socrata_data(url: str, filters: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
    """
    Fetch data from a Socrata dataset.
    
    Args:
        url: Socrata API endpoint (ends with .json)
        filters: Optional filters (e.g., {"status": "Issued"})
        limit: Number of records to fetch
    
    Returns:
        List of records
    """
    try:
        # Build query with SoQL syntax
        params = {"$limit": limit}
        
        if filters:
            where_clauses = []
            for key, value in filters.items():
                if isinstance(value, str):
                    where_clauses.append(f"{key}='{value}'")
                else:
                    where_clauses.append(f"{key}={value}")
            if where_clauses:
                params["$where"] = " AND ".join(where_clauses)
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        logger.info(f"✓ Fetched {len(response.json())} records from Socrata")
        return response.json()
    
    except requests.RequestException as e:
        logger.error(f"✗ Error fetching Socrata data: {e}")
        return []


def fetch_arcgis_data(
    base_url: str,
    where: str = "1=1",
    limit: int = 100,
    out_fields: str = "*"
) -> List[Dict]:
    """
    Fetch data from an ArcGIS FeatureServer.
    
    Args:
        base_url: ArcGIS FeatureServer URL (without /query)
        where: WHERE clause for filtering
        limit: Number of records to fetch
        out_fields: Fields to return
    
    Returns:
        List of features
    """
    try:
        url = f"{base_url}/query"
        params = {
            "where": where,
            "outFields": out_fields,
            "returnGeometry": "true",
            "f": "json",
            "resultOffset": 0,
            "resultRecordCount": limit
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        features = data.get("features", [])
        
        logger.info(f"✓ Fetched {len(features)} features from ArcGIS")
        return [f["attributes"] for f in features]
    
    except requests.RequestException as e:
        logger.error(f"✗ Error fetching ArcGIS data: {e}")
        return []


def normalize_permit_record(raw_data: Dict, city: str) -> Dict:
    """
    Normalize a raw permit record to standard schema.
    
    Args:
        raw_data: Raw permit data from source
        city: City name (determines field mapping)
    
    Returns:
        Normalized permit record
    """
    source_config = FREE_DATA_SOURCES.get(city, {})
    fields_map = source_config.get("fields", {})
    
    normalized = {
        "city": city,
        "permit_id": raw_data.get(fields_map.get("permit_id", "permit_id"), "Unknown"),
        "address": _extract_address(raw_data, fields_map),
        "permit_type": raw_data.get(fields_map.get("permit_type", "permit_type"), "Unknown"),
        "description": raw_data.get(fields_map.get("description", "description"), ""),
        "valuation": _extract_valuation(raw_data, fields_map),
        "status": raw_data.get(fields_map.get("status", "status"), "Unknown"),
        "filed_date": raw_data.get(fields_map.get("submitted_date", "submitted_date")),
        "issued_date": raw_data.get(fields_map.get("issued_date", "issued_date")),
        "applicant": _extract_applicant(raw_data, fields_map),
        "contractor": raw_data.get(fields_map.get("contractor_company", "contractor"), ""),
        "owner": "",  # Can be enriched via OSINT
        "source_url": source_config.get("socrata", ""),
        "raw_json": raw_data
    }
    
    return {k: v for k, v in normalized.items() if v is not None}


def _extract_address(data: Dict, fields_map: Dict) -> str:
    """Extract and combine address components."""
    address_key = fields_map.get("address", "address")
    if isinstance(address_key, str):
        return data.get(address_key, "")
    # If multiple fields (e.g., "street_number,street_name")
    address_parts = []
    for key in address_key.split(","):
        val = data.get(key.strip(), "")
        if val:
            address_parts.append(str(val))
    return " ".join(address_parts)


def _extract_valuation(data: Dict, fields_map: Dict) -> Optional[float]:
    """Extract valuation and convert to float."""
    valuation_key = fields_map.get("valuation", "valuation")
    value = data.get(valuation_key)
    if value:
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    return None


def _extract_applicant(data: Dict, fields_map: Dict) -> str:
    """Extract applicant name, combining first/last if needed."""
    applicant_key = fields_map.get("applicant", "applicant")
    
    # Try direct applicant field
    if applicant_key in data:
        return str(data[applicant_key])
    
    # Try first + last name
    first = data.get(fields_map.get("applicant_first_name", "applicant_first_name"), "")
    last = data.get(fields_map.get("applicant_last_name", "applicant_last_name"), "")
    
    return f"{first} {last}".strip()


def fetch_city_permits(city: str, limit: int = 100, filters: Optional[Dict] = None) -> List[Dict]:
    """
    Fetch permits for a specific city using pre-configured sources.
    
    Args:
        city: City name (must be in FREE_DATA_SOURCES)
        limit: Number of records to fetch
        filters: Optional filters (e.g., {"status": "Issued"})
    
    Returns:
        List of normalized permit records
    """
    if city not in FREE_DATA_SOURCES:
        logger.error(f"✗ City {city} not in pre-configured sources")
        return []
    
    config = FREE_DATA_SOURCES[city]
    
    # Try Socrata first
    if "socrata" in config:
        logger.info(f"Fetching permits from {city} (Socrata)...")
        raw_permits = fetch_socrata_data(config["socrata"], filters=filters, limit=limit)
        
        # Normalize each record
        normalized_permits = [normalize_permit_record(p, city) for p in raw_permits]
        return normalized_permits
    
    logger.warning(f"No Socrata endpoint found for {city}")
    return []


def list_available_cities() -> List[str]:
    """List all pre-configured cities."""
    return list(FREE_DATA_SOURCES.keys())


def get_source_config(city: str) -> Optional[Dict]:
    """Get source configuration for a city."""
    return FREE_DATA_SOURCES.get(city)
