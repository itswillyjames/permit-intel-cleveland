# Multi-vertical curation service for permit intelligence packaging

VERTICALS = {
    "mortgage_broker": {
        "description": "Financing gap opportunities and bridge lending",
        "key_fields": ["owner", "valuation", "timeline", "property_tax"],
        "leverage_angle": "financing",
    },
    "general_contractor": {
        "description": "Scope of work, bidding opportunities, subcontractor leads",
        "key_fields": ["permit_type", "description", "contractor", "timeline"],
        "leverage_angle": "scope_arbitrage",
    },
    "electrician": {
        "description": "Electrical work required, project timeline, GC contact",
        "key_fields": ["description", "permit_type", "contractor", "timeline"],
        "leverage_angle": "vendor_arbitrage",
    },
    "hvac_specialist": {
        "description": "HVAC opportunities, timing, and GC/PI contact",
        "key_fields": ["description", "permit_type", "contractor", "timeline"],
        "leverage_angle": "vendor_arbitrage",
    },
    "supplier": {
        "description": "Material lead, project size, and timeline",
        "key_fields": ["description", "valuation", "permit_type", "timeline"],
        "leverage_angle": "supplier_network",
    },
}

def curate_permit(permit, enrichment_data=None):
    """
    Curate a permit into multi-vertical intelligence packages.
    
    Args:
        permit: SQLAlchemy Permit model instance
        enrichment_data: dict of enrichment information
    
    Returns:
        list of dicts, each representing a curated package for a vertical
    """
    packages = []
    
    for vertical_key, vertical_info in VERTICALS.items():
        package = {
            "permit_id": permit.id,
            "permit_number": permit.permit_id,
            "vertical": vertical_key,
            "vertical_description": vertical_info["description"],
            "leverage_angle": vertical_info["leverage_angle"],
            "content": {
                "address": permit.address,
                "city": permit.city,
                "description": permit.description,
                "valuation": permit.valuation,
                "status": permit.status,
                "permit_type": permit.permit_type,
                "contractor": permit.contractor,
                "owner": permit.owner,
                "source_url": permit.source_url,
                "key_fields": [
                    {
                        "name": field,
                        "value": getattr(permit, field.lower(), None)
                    }
                    for field in vertical_info["key_fields"]
                ]
            }
        }
        packages.append(package)
    
    return packages

def identify_cross_sells(packages):
    """
    Identify cross-sell and referral opportunities between packages.
    
    Args:
        packages: list of curated packages
    
    Returns:
        list of dicts describing referral opportunities
    """
    cross_sells = []
    
    # Example: GC can refer to electrician for electrical work
    opportunities = [
        {
            "from_vertical": "general_contractor",
            "to_vertical": "electrician",
            "referral_fee": "10% of contract",
            "pitch": "Refer electrical subcontractor for faster project completion",
        },
        {
            "from_vertical": "general_contractor",
            "to_vertical": "hvac_specialist",
            "referral_fee": "10% of contract",
            "pitch": "Refer HVAC specialist to ensure on-time system installation",
        },
        {
            "from_vertical": "mortgage_broker",
            "to_vertical": "general_contractor",
            "referral_fee": "0.5% of project valuation",
            "pitch": "Connect client with vetted contractor to complete project faster",
        },
    ]
    
    for opp in opportunities:
        # Check if both verticals are in packages
        from_pkg = next((p for p in packages if p["vertical"] == opp["from_vertical"]), None)
        to_pkg = next((p for p in packages if p["vertical"] == opp["to_vertical"]), None)
        
        if from_pkg and to_pkg:
            cross_sells.append({
                "from_vertical": opp["from_vertical"],
                "to_vertical": opp["to_vertical"],
                "referral_fee": opp["referral_fee"],
                "pitch": opp["pitch"],
                "expected_value": from_pkg["content"].get("valuation", 0) * 0.001,
            })
    
    return cross_sells

