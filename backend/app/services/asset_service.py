# Asset generation service - creates sales and outreach materials

def generate_assets(permit, package, vertical):
    """
    Generate a complete asset pack for a curated package.
    
    Args:
        permit: SQLAlchemy Permit model
        package: dict, curated package from curation_service
        vertical: str, vertical code
    
    Returns:
        dict with all sales assets (pitches, NDA, one-pager, call script)
    """
    return {
        "permit_id": permit.id,
        "permit_number": permit.permit_id,
        "vertical": vertical,
        "assets": {
            "email_pitch": generate_email_pitch(permit, vertical),
            "linkedin_pitch": generate_linkedin_pitch(permit, vertical),
            "one_pager": generate_one_pager(permit, vertical),
            "call_script": generate_call_script(permit, vertical),
            "objection_handling": generate_objection_handling(vertical),
            "nda_template": generate_nda_template(),
            "deal_terms": generate_deal_terms(permit, vertical),
        }
    }

def generate_email_pitch(permit, vertical):
    """Generate an email pitch for a specific vertical."""
    
    templates = {
        "mortgage_broker": {
            "subject": f"Commercial Finance Opportunity - {permit.city} Project",
            "body": f"""Hi {{prospect_name}},

I work with a network of project intelligence specialists who identify high-value commercial construction opportunities before they hit the market.

**Project Details:**
- Location: {permit.address}, {permit.city}
- Type: {permit.permit_type}
- Valuation: ${permit.valuation:,.0f}
- Status: {permit.status}

**Why This Matters for You:**
Projects of this size often require bridge financing, construction loans, or equipment financing. The owner/GC may be facing a capital gap as the project progresses.

**What You Get:**
1. Full permit details (filed date, applicant, contractor info)
2. Owner financial profile (if available)
3. Property assessment & tax status
4. Your likelihood of the deal

**Investment:** $5,000 for the full intel package | 15% of origination fee if closed

Ready for a quick call?

Best,
[Your Name]
[Title]
[Phone]"""
        },
        "general_contractor": {
            "subject": f"Qualified Subcontractor Lead - {permit.city}",
            "body": f"""Hi {{prospect_name}},

New commercial project with potential subcontracting work:

**Project Snapshot:**
- Address: {permit.address}, {permit.city}
- Type: {permit.permit_type}
- Scope: {permit.description}
- Valuation: ${permit.valuation:,.0f}
- GC: {{permit.contractor or 'TBD'}}

**Next Steps:**
1. You review the scope
2. Decide if interested
3. I provide GC contact and bid packet

**Cost:** $2,500 for lead + contact | $5,000 for full bid intelligence

Interested?

Best,
[Your Name]"""
        },
        "electrician": {
            "subject": f"Electrical Subcontracting Work - {permit.city}",
            "body": f"""Hi {{prospect_name}},

Electrical scope identified on new {permit.permit_type} project in {permit.city}.

**Details:**
{permit.description}

Valuation: ${permit.valuation:,.0f}

GC ready to bid. Interested in the lead?

$1,500 for GC contact | 5% of contract value as referral

Talk soon,
[Your Name]"""
        },
        "supplier": {
            "subject": f"Material Opportunity - {permit.city} Project",
            "body": f"""Hi {{prospect_name}},

New {permit.permit_type} project identified with likely material orders.

{permit.description}

Project size: ${permit.valuation:,.0f}

Early visibility = better margin negotiation. Interested?

$3,000 for lead | 2% of material orders as ongoing fee

Best,
[Your Name]"""
        }
    }
    
    template = templates.get(vertical, {
        "subject": f"Project Opportunity Alert",
        "body": f"Project alert: {permit.address}, {permit.city}\nValuation: ${permit.valuation:,.0f}\nInterested?"
    })
    
    return template

def generate_linkedin_pitch(permit, vertical):
    """Generate a LinkedIn message version of the pitch."""
    return f"""Hi {{name}},

I came across a {permit.permit_type} project in {permit.city} that might interest you.

{permit.address} | Valuation: ${permit.valuation:,.0f}

Would a {{vertical_benefit}} opportunity be valuable right now?

Open to a quick conversation?

{{name_signature}}"""

def generate_one_pager(permit, vertical):
    """Generate a one-page opportunity brief."""
    return {
        "title": f"Intelligence Brief: {permit.address}",
        "project_overview": {
            "address": permit.address,
            "city": permit.city,
            "type": permit.permit_type,
            "valuation": f"${permit.valuation:,.0f}",
            "status": permit.status,
            "filed_date": permit.filed_date,
            "issued_date": permit.issued_date,
        },
        "scope_summary": permit.description,
        "key_parties": {
            "applicant": permit.applicant,
            "contractor": permit.contractor,
            "owner": permit.owner,
        },
        "opportunity_angle": f"Vertical: {vertical}",
        "next_actions": [
            "1. Review project scope",
            "2. Reach out to GC/Owner (contact provided)",
            "3. Submit proposal/bid within 48 hours",
        ],
        "source": permit.source_url,
    }

def generate_call_script(permit, vertical):
    """Generate a call script for prospect outreach."""
    
    scripts = {
        "mortgage_broker": """
[OPENING]
"Hi [name], thanks for taking the call. I help commercial lenders identify project finance opportunities before they become common knowledge. I came across your firm because of your strong track record in [market]. Do you have 5 minutes?"

[VALUE PROP]
"We track commercial projects from the permit stage. What we're seeing is that projects valued over $1M frequently need bridge or gap financing. Right now, I'm looking at a ${permit.valuation}M project in [city] that fits this profile perfectly."

[DISCOVER]
"What does your typical construction finance deal look like?"
"How long is your typical close timeline?"

[PITCH]
"Based on this project, I think there's a real origination fee opportunity here. We provide the lead, owner contact, and preliminary financial profile. You assess and close the deal."

[CLOSE]
"Can I send you the lead packet? We can follow up Thursday."
""",
        "general_contractor": """
[OPENING]
"Hi [name], I track new commercial projects in your market specifically for GCs. I came across your firm and wanted to reach out about a potential bid opportunity."

[OPPORTUNITY]
"A {permit.permit_type} project just came through—{permit.address} in {permit.city}. Size: ${permit.valuation}. Scope includes [describe from permit]."

[DISCOVER]
"Is this the type of project you typically bid on?"
"Do you already have a relationship with the prime on this one?"

[PITCH]
"I can get you the GC contact and full bid details. For the cost of the lead, you get first-mover advantage in scope outreach."

[CLOSE]
"Interested? I can email the packet within the hour."
""",
    }
    
    return scripts.get(vertical, "Generic call script: Introduce yourself, present opportunity, ask about interest, propose next step.")

def generate_objection_handling(vertical):
    """Generate objection handling guidance."""
    
    handling = {
        "mortgage_broker": {
            "I don't have capacity right now": "That's fair. This is a low-touch. We do the sourcing, you assess. Even 1-2 deals/quarter could be worth a serious conversation.",
            "How do I know this is legitimate?": "Great question. [Provide references]. Also—the permit is public record. You can verify the project, address, and scope independently.",
            "Your pricing is high": "The origination fee is usually 150-250 bps. If you close the deal, the intel cost ($X) is less than 0.5% of the total deal. Worth discussing?",
        },
        "general_contractor": {
            "Is the GC even accessible?": "Yes. We source direct contact for the PM or estimating lead. They're actively recruiting subs right now.",
            "I don't know if I can compete": "You won't know until you bid. Early visibility is your advantage. Plus, I can share what other subs bid.",
            "Can't you just give me the lead for free?": "Wish I could. This is how I stay in business. But think of it as a qualified lead—you save 20+ hours vs. cold calling.",
        }
    }
    
    return handling.get(vertical, {})

def generate_nda_template():
    """Generate a simple NDA template."""
    return """
MUTUAL NON-DISCLOSURE AGREEMENT

This Agreement is made as of [date] between:

[Company Name] ("Discloser")

and

[Recipient Name] ("Recipient")

WHEREAS, Discloser desires to disclose certain confidential information to Recipient for the purpose of [purpose].

NOW, THEREFORE, in consideration of the mutual covenants herein:

1. CONFIDENTIAL INFORMATION
Recipient agrees that all information disclosed by Discloser, including but not limited to project details, financial data, owner/contractor contacts, and market intelligence, shall be treated as confidential.

2. PERMITTED USE
Recipient may use Confidential Information solely for the purpose stated above and not for any competitive purpose.

3. RETURN OF INFORMATION
Upon request or termination of this Agreement, Recipient shall return or destroy all Confidential Information.

4. TERM
This Agreement shall remain in effect for [12 months / 2 years] from the date hereof.

AGREED AND ACCEPTED:

Discloser: ___________________  Date: _______
Recipient: __________________  Date: _______
"""

def generate_deal_terms(permit, vertical):
    """Generate deal term options for monetization."""
    
    verticals_terms = {
        "mortgage_broker": {
            "option_1": {
                "name": "Fixed Fee",
                "description": "One-time intel package fee",
                "price": "$10,000",
                "includes": ["Full permit details", "Owner financial data", "Tax status", "Estimated closing probability"]
            },
            "option_2": {
                "name": "Hybrid: Fixed + Success",
                "description": "Lower upfront + origination fee if deal closes",
                "price": "$2,500 + 10% of origination fee",
                "includes": ["Same as above", "Monthly updates until close"]
            },
            "option_3": {
                "name": "Revenue Share",
                "description": "No upfront cost; we take small cut of deal",
                "price": "3% of origination fee",
                "includes": ["Full support", "Deal term negotiation", "Monthly performance tracking"]
            },
            "option_4": {
                "name": "Retainer + Volume Discount",
                "description": "Monthly alert service + bulk discount",
                "price": "$5,000/month for 10+ leads/month",
                "includes": ["Unlimited project alerts", "Deep financial analysis", "Priority support"]
            }
        },
        "general_contractor": {
            "option_1": {
                "name": "Lead Only",
                "description": "Permit data + GC contact",
                "price": "$2,500 per lead",
                "includes": ["Permit details", "GC PM contact", "Preliminary scope"]
            },
            "option_2": {
                "name": "Full Intelligence Pack",
                "description": "Lead + competitive intelligence",
                "price": "$5,000 per lead",
                "includes": ["Everything above", "Estimated sub pricing", "Historical GC relationships"]
            },
            "option_3": {
                "name": "Referral Fee",
                "description": "We introduce you to GC, we take referral %",
                "price": "5-10% of first contract",
                "includes": ["Direct GC intro", "Account management"]
            }
        }
    }
    
    return verticals_terms.get(vertical, {
        "option_1": {
            "name": "Standard Package",
            "price": "$5,000",
            "description": "Full permit intelligence"
        }
    })
