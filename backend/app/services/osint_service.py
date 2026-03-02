"""
Auto-OSINT enrichment service - Fetch free public data to enrich permits
Uses only free, legal, public data sources
"""
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Free public data sources
OSINT_SOURCES = {
    "google_news": "https://news.google.com/search",  # Via RSS
    "business_registry": "https://www.sec.gov/cgi-bin/browse-edgar",  # SEC EDGAR
    "propertyshark": "https://www.propertyshark.com",  # Property data
}


def enrich_permit(permit_id: int, permit_data: Dict) -> List[Dict]:
    """
    Enrich a permit with free public data.
    
    Args:
        permit_id: ID in database
        permit_data: Permit record (address, owner, contractor, etc.)
    
    Returns:
        List of enrichment records with source URLs
    """
    enrichments = []
    
    # 1. Business registration lookup
    if permit_data.get("contractor"):
        business_data = fetch_business_registration(permit_data["contractor"])
        if business_data:
            enrichments.append({
                "type": "business_registration",
                "data": business_data,
                "url": "https://www.sec.gov/cgi-bin/browse-edgar"
            })
    
    # 2. News mentions
    if permit_data.get("address") or permit_data.get("contractor"):
        news_data = fetch_news_mentions(
            permit_data.get("contractor", ""),
            permit_data.get("city", "")
        )
        if news_data:
            enrichments.append({
                "type": "news",
                "data": news_data,
                "url": "https://news.google.com"
            })
    
    # 3. Public records (if available)
    if permit_data.get("owner"):
        records_data = fetch_public_records(permit_data["owner"])
        if records_data:
            enrichments.append({
                "type": "public_records",
                "data": records_data,
                "url": "https://www.publicrecords.com"
            })
    
    # 4. Property valuation estimate
    if permit_data.get("address") and permit_data.get("city"):
        property_data = fetch_property_estimate(
            permit_data["address"],
            permit_data["city"]
        )
        if property_data:
            enrichments.append({
                "type": "property_estimate",
                "data": property_data,
                "url": "https://www.zillow.com"
            })
    
    logger.info(f"✓ Enriched permit {permit_id} with {len(enrichments)} data sources")
    return enrichments


def fetch_business_registration(company_name: str) -> Optional[Dict]:
    """
    Fetch business registration info from SEC EDGAR (free, public).
    
    Args:
        company_name: Company name to search
    
    Returns:
        Business info dict with URL
    """
    try:
        # SEC EDGAR search
        search_url = "https://www.sec.gov/cgi-bin/browse-edgar"
        params = {
            "company": company_name,
            "owner": "exclude",
            "action": "getcompany",
            "output": "json"
        }
        
        response = requests.get(search_url, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        ciks = data.get("cik_lookup", [])
        
        if ciks:
            logger.info(f"✓ Found SEC registration for {company_name}")
            return {
                "company_name": company_name,
                "cik": ciks[0]["cik_str"] if ciks else None,
                "registered": True,
                "source": "SEC EDGAR"
            }
    except Exception as e:
        logger.debug(f"Could not fetch SEC data for {company_name}: {e}")
    
    return None


def fetch_news_mentions(company_name: str, city: str) -> Optional[Dict]:
    """
    Fetch recent news mentions (via free news API or RSS).
    
    Args:
        company_name: Company to search
        city: City for geo-targeting
    
    Returns:
        News articles list
    """
    try:
        # Using NewsAPI free tier (requires API key, but showing pattern)
        # For truly free, could use RSS from news.google.com
        
        query = f"{company_name} {city} construction OR permit OR development"
        
        # This is a placeholder showing how to structure OSINT
        logger.info(f"Would search news for: {query}")
        
        return {
            "query": query,
            "articles": [],
            "note": "Free news integration available via RSS or free tier APIs"
        }
    except Exception as e:
        logger.debug(f"Could not fetch news: {e}")
    
    return None


def fetch_public_records(person_name: str) -> Optional[Dict]:
    """
    Fetch public records (court, UCC, property).
    Many states offer free public records searches.
    
    Args:
        person_name: Person name to search
    
    Returns:
        Public records summary
    """
    try:
        # Free public record sources include:
        # - County courthouse online systems
        # - Property appraiser websites
        # - UCC filing searches
        
        logger.info(f"Would search public records for: {person_name}")
        
        return {
            "name": person_name,
            "records": [],
            "note": "Free public records available via county websites"
        }
    except Exception as e:
        logger.debug(f"Could not fetch public records: {e}")
    
    return None


def fetch_property_estimate(address: str, city: str) -> Optional[Dict]:
    """
    Fetch property valuation estimate (Zillow, Trulia, etc.).
    Some provide free data via RSS/API.
    
    Args:
        address: Property address
        city: City
    
    Returns:
        Property estimate data
    """
    try:
        # Zillow, Redfin offer public estimates
        # This shows the structure; real implementation would call APIs
        
        query = f"{address}, {city}"
        logger.info(f"Would fetch property estimate for: {query}")
        
        return {
            "address": query,
            "estimate": None,
            "note": "Property estimates available via Zillow API (free tier)"
        }
    except Exception as e:
        logger.debug(f"Could not fetch property data: {e}")
    
    return None


def identify_financial_health(owner_name: str, contractor_name: str) -> Dict:
    """
    Assess financial health using public data.
    
    Args:
        owner_name: Property owner
        contractor_name: General contractor
    
    Returns:
        Financial health assessment
    """
    assessment = {
        "owner_registered": bool(fetch_business_registration(owner_name) if owner_name else False),
        "contractor_registered": bool(fetch_business_registration(contractor_name) if contractor_name else False),
        "risk_level": "medium",  # Would be ML model in future
        "indicators": []
    }
    
    return assessment


def generate_osint_summary(enrichments: List[Dict]) -> Dict:
    """
    Generate a summary of OSINT findings.
    
    Args:
        enrichments: List of enrichment records
    
    Returns:
        Summary of findings with key insights
    """
    summary = {
        "total_sources": len(enrichments),
        "types": list(set(e["type"] for e in enrichments)),
        "findings": [],
        "risk_level": "unknown",
        "recommendation": "Manual review recommended for high-value opportunities"
    }
    
    # Extract key findings
    for enr in enrichments:
        if enr["type"] == "business_registration" and enr["data"].get("registered"):
            summary["findings"].append(f"Contractor registered: {enr['data'].get('company_name')}")
        elif enr["type"] == "news" and enr["data"].get("articles"):
            summary["findings"].append(f"Recent news mentions: {len(enr['data']['articles'])} articles")
    
    return summary
