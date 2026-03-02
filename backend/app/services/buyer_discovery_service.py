# Buyer discovery and qualification service

def generate_buyer_discovery_plan(permit, vertical):
    """
    Generate a buyer discovery plan for a specific permit + vertical.
    
    Args:
        permit: SQLAlchemy Permit model
        vertical: str, vertical code (e.g., "mortgage_broker")
    
    Returns:
        dict with discovery strategy and queries
    """
    city = permit.city or "Unknown City"
    
    discovery_plans = {
        "mortgage_broker": {
            "why_they_pay": "High-value commercial projects need bridge/construction financing",
            "queries": [
                f"site:linkedin.com '{city}' mortgage broker commercial real estate",
                f"'{city}' construction financing lenders",
                f"site:crunchbase.com construction finance lender '{city}'",
            ],
            "directories": [
                f"Local Chamber of Commerce: {city}, business lending directory",
                f"SBA Registered Lenders in {city}",
                f"FINRA Broker Dealer database (FINRA BrokerCheck)",
            ],
            "qualification_questions": [
                "Do you provide bridge financing for commercial construction?",
                "What is your typical LTV and interest rate range?",
                "How quickly can you close on a construction project?",
                "Have you financed projects in the $1M-$10M range?",
            ]
        },
        "general_contractor": {
            "why_they_pay": "Need subcontractor leads, scope insights, and bidding intelligence",
            "queries": [
                f"site:linkedin.com '{city}' general contractor commercial",
                f"'{city}' commercial construction company",
                f"site:contractorslicense.org {city} general contractor",
            ],
            "directories": [
                f"{city} Contractors Licensing Board (licensed GCs)",
                f"ABC (Associated General Contractors) chapter in {city}",
                f"AGC directory: associated general contractors",
            ],
            "qualification_questions": [
                "What types of commercial projects do you typically bid on?",
                "Do you use subcontractor lead services?",
                "How far in advance do you identify subcontractors?",
                "Would you pay for pre-qualified specialist referrals?",
            ]
        },
        "electrician": {
            "why_they_pay": "Direct lead on electrical work needed; opportunity to bid",
            "queries": [
                f"site:linkedin.com '{city}' licensed electrician commercial",
                f"'{city}' commercial electrician electrical contractor",
                f"site:electricallicensing.org {city} master electrician",
            ],
            "directories": [
                f"{city} Electricians Licensing Board (licensed electricians)",
                f"Local electrical union (IBEW) chapter in {city}",
                f"Yelp/Google: commercial electricians '{city}'",
            ],
            "qualification_questions": [
                "Are you licensed for commercial electrical work?",
                "What is your typical project size and scope?",
                "How do you source new construction projects?",
                "Would you pay a finder's fee for direct project leads?",
            ]
        },
        "supplier": {
            "why_they_pay": "Material orders from known projects; can negotiate terms",
            "queries": [
                f"site:linkedin.com '{city}' building materials supplier",
                f"'{city}' commercial building materials distributor",
                f"site:thomasnet.com building materials supplier {city}",
            ],
            "directories": [
                f"{city} Builders Association (material suppliers)",
                f"Thomas Net: industrial suppliers in {city}",
                f"National Association of Wholesaler-Distributors (NAW)",
            ],
            "qualification_questions": [
                "What types of building materials do you supply?",
                "Do you offer project financing or payment terms?",
                "What is your typical order size?",
                "Are you interested in early-project material forecasting?",
            ]
        }
    }
    
    plan = discovery_plans.get(vertical, {
        "why_they_pay": "Value from intelligence",
        "queries": [f"'{city}' commercial business services"],
        "directories": [f"{city} Better Business Bureau", f"{city} Chamber of Commerce"],
        "qualification_questions": ["Are you interested in permit intelligence?"]
    })
    
    return {
        "permit_id": permit.id,
        "permit_number": permit.permit_id,
        "vertical": vertical,
        "city": city,
        "discovery_plan": plan,
        "next_steps": [
            f"1. Use queries above to identify {vertical}s in {city}",
            f"2. Cross-reference with LinkedIn to personalize outreach",
            f"3. Check licensing/business registrations for credibility",
            f"4. Reach out with tailored pitch (see assets)",
            f"5. Ask qualification questions to assess fit",
        ]
    }

def generate_outreach_pitch(permit, vertical):
    """Generate a templated outreach pitch for a vertical."""
    
    pitches = {
        "mortgage_broker": f"""
Subject: Commercial Construction Finance Opportunity - {permit.address}

Hi {{name}},

I'm reaching out because I track high-value commercial projects in your market.

I just identified a {permit.permit_type.lower()} project at {{permit.address}} valued at ${permit.valuation:,.0f} 
in {permit.city}. The project is currently {{permit.status}}, and based on typical timelines, 
the owner/GC may be facing a financing gap or cash flow crunch.

This could be an ideal opportunity for:
- Bridge financing (accelerate development)
- Construction financing (reduce project risk)
- Supplier financing (vendor relationships)

Would you be interested in a brief call to discuss? I can provide the full permit details, 
owner contact info, and contractor intelligence.

Best, [Your Name]
        """,
        "general_contractor": f"""
Subject: Subcontractor Lead - {permit.permit_type} Project in {permit.city}

Hi {{name}},

I specialize in identifying high-value construction projects for contractors.

A {permit.permit_type.lower()} project just came through in {permit.city} at {{permit.address}} 
valued at ${permit.valuation:,.0f}. The scope includes: {{permit.description}}.

Identified needs:
- Prime contractor: {{permit.contractor or 'TBD'}}
- Key scope: {{permit.description}}
- Timeline: {{permit.status or 'Typical timeline'}}

I can connect you with the GC or provide full bid intelligence. Interested?

Best, [Your Name]
        """,
        "electrician": f"""
Subject: Electrical Subcontracting Opportunity - {permit.city}

Hi {{name}},

New commercial project with electrical scope identified.

Project: {permit.address}, {permit.city}
Scope: {{permit.description}}
Valuation: ${permit.valuation:,.0f}
Status: {{permit.status}}

If interested in bidding, I can provide GC contact and full project details.

Quick call?

Best, [Your Name]
        """,
    }
    
    return pitches.get(vertical, f"""
Subject: New {permit.permit_type} Project in {permit.city}

Hi {{name}},

New project alert for your consideration: {permit.address}

Interested in the details?

Best, [Your Name]
    """)
