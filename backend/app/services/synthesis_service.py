# Opportunity synthesis service - generates leverage angles and proof points

def synthesize_opportunity(permit, score):
    """
    Generate 3 leverage angles and proof points for a permit.
    
    Args:
        permit: SQLAlchemy Permit model
        score: SQLAlchemy Score model (scoring result)
    
    Returns:
        dict with leverage angles and proof points
    """
    angles = []
    
    # Angle 1: Delay Arbitrage
    if score.delay_score > 0.4:
        angles.append({
            "angle": "delay_arbitrage",
            "title": "Project Stalled - Expedite for Profit",
            "description": "This project shows signs of delay. Your client can expedite completion, creating opportunities for:",
            "opportunities": [
                "Bridge lending to accelerate development",
                "Fast-track permitting/inspection services",
                "Specialized subcontractors (premium rates for fast delivery)",
            ],
            "proof_points": [
                {
                    "claim": f"Project valuation: ${permit.valuation:,.0f}",
                    "source": permit.source_url,
                },
                {
                    "claim": f"Current status: {permit.status}",
                    "source": permit.source_url,
                },
                {
                    "claim": "Typical commercial project delays: 20-30% cost overruns",
                    "source": "Industry data (FMI Construction Industry Trends)",
                },
            ]
        })
    
    # Angle 2: Vendor/Scope Arbitrage
    if "electrical" in (permit.description or "").lower() or "hvac" in (permit.description or "").lower() or "sprinkler" in (permit.description or "").lower():
        angles.append({
            "angle": "vendor_arbitrage",
            "title": "Specialized Subcontractor Opportunity",
            "description": "Identified specialized scope (electrical, HVAC, sprinkler). GC/PI likely seeking vetted vendors. Supplier can win contract.",
            "opportunities": [
                "Win subcontracting bid via fast, reliable lead",
                "Negotiate premium rates for urgency/expertise",
                "Build relationship for future projects",
            ],
            "proof_points": [
                {
                    "claim": f"Permit type: {permit.permit_type}",
                    "source": permit.source_url,
                },
                {
                    "claim": f"Key scope: {permit.description[:100]}...",
                    "source": permit.source_url,
                },
                {
                    "claim": "Subcontractors report 25-40% higher rates for expedited work",
                    "source": "Construction contractor surveys (ENR)",
                },
            ]
        })
    
    # Angle 3: Financing/Capital Gap
    if permit.valuation and permit.valuation > 500000:
        angles.append({
            "angle": "financing_arbitrage",
            "title": "Capital Gap from Valuation Surge",
            "description": "Large project valuation suggests owner/GC may face cash flow or construction financing gaps.",
            "opportunities": [
                "Offer bridge financing at 2-4 points above prime",
                "Supplier financing for materials",
                "Hard money lending for delayed draw scenarios",
            ],
            "proof_points": [
                {
                    "claim": f"Project valuation: ${permit.valuation:,.0f}",
                    "source": permit.source_url,
                },
                {
                    "claim": f"Address: {permit.address}",
                    "source": permit.source_url,
                },
                {
                    "claim": "Construction projects >$500k often require bridge financing (40% of projects)",
                    "source": "Loan Syndications and Trading Association (LSTA)",
                },
            ]
        })
    
    return {
        "permit_id": permit.id,
        "permit_number": permit.permit_id,
        "address": permit.address,
        "city": permit.city,
        "win_score": round(score.win_score, 2),
        "leverage_angles": angles,
        "initial_buyer_categories": _identify_buyers(permit),
    }

def _identify_buyers(permit):
    """Identify initial buyer categories based on permit characteristics."""
    buyers = []
    
    if permit.valuation and permit.valuation > 1000000:
        buyers.append({
            "type": "Mortgage Broker / Commercial Lender",
            "why_they_pay": "High-valuation projects often need bridge or construction financing",
            "estimated_deal_size": "0.5-1% of project valuation",
        })
    
    if "commercial" in (permit.permit_type or "").lower() or "retail" in (permit.description or "").lower():
        buyers.append({
            "type": "General Contractor",
            "why_they_pay": "Need subcontractor leads and scope intelligence",
            "estimated_deal_size": "$5k-$25k per lead package",
        })
    
    if any(keyword in (permit.description or "").lower() for keyword in ["electrical", "hvac", "sprinkler", "plumbing"]):
        buyers.append({
            "type": "Specialized Subcontractor (Electrician, HVAC, etc.)",
            "why_they_pay": "High-margin subcontracting bids on known projects",
            "estimated_deal_size": "5-10% of contract value",
        })
    
    buyers.append({
        "type": "Permit Expediting Service",
        "why_they_pay": "Delayed projects are their ideal customers",
        "estimated_deal_size": "$10k-$50k per project",
    })
    
    return buyers
