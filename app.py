import os
import requests
import csv
from flask import Flask, jsonify, render_template, Response
from io import StringIO

app = Flask(__name__, static_folder="static", template_folder="templates")

# ----------------------------
# DATA SOURCES (ALL FREE)
# ----------------------------

PERMIT_URL = "https://services2.arcgis.com/CyVvlIiUfRBmMQuu/arcgis/rest/services/Building_Permits_Applications_view/FeatureServer/1/query"

PARCEL_URL = "https://gis.cuyahogacounty.us/arcgis/rest/services/RealEstate/MapServer/0/query"

CENSUS_URL = "https://api.census.gov/data/2022/acs/acs5"

# ----------------------------
# CORE PIPELINE
# ----------------------------

def fetch_permits(limit=50):
    params = {
        "f": "json",
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "false",
        "resultRecordCount": str(limit)
    }

    r = requests.get(PERMIT_URL, params=params, timeout=60)
    data = r.json()

    results = []

    for f in data.get("features", []):
        p = f.get("attributes", {})

        permit = {
            "permit_id": p.get("PERMIT_NUMBER") or p.get("OBJECTID"),
            "description": p.get("WORK_DESCRIPTION") or "",
            "status": p.get("STATUS") or "",
            "value": float(p.get("ESTIMATED_COST") or 0),
            "address": p.get("SITE_ADDRESS") or "",
            "owner": p.get("OWNER_NAME") or ""
        }

        enrich_parcel(permit)
        enrich_census(permit)

        permit["score"] = score(permit)
        permit["deal_type"] = classify(permit)

        results.append(permit)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results

# ----------------------------
# ENRICHMENT
# ----------------------------

def enrich_parcel(p):
    try:
        if not p["address"]:
            return

        params = {
            "f": "json",
            "where": f"SITE_ADDR LIKE '%{p['address']}%'",
            "outFields": "OWNER_NAME,MARKET_VALUE,LAND_USE,YEAR_BUILT",
            "returnGeometry": "false"
        }

        r = requests.get(PARCEL_URL, params=params, timeout=30)
        data = r.json()

        if data.get("features"):
            attr = data["features"][0]["attributes"]
            p["assessed_value"] = attr.get("MARKET_VALUE")
            p["land_use"] = attr.get("LAND_USE")
            p["year_built"] = attr.get("YEAR_BUILT")
        else:
            p["assessed_value"] = None

    except:
        p["assessed_value"] = None


def enrich_census(p):
    try:
        params = {
            "get": "B19013_001E",
            "for": "tract:*",
            "in": "state:39 county:035"
        }

        r = requests.get(CENSUS_URL, params=params, timeout=30)
        data = r.json()

        if len(data) > 1:
            p["median_income_area"] = data[1][0]
        else:
            p["median_income_area"] = None

    except:
        p["median_income_area"] = None


# ----------------------------
# SCORING ENGINE
# ----------------------------

def score(p):
    s = 0

    if p["value"] > 2000000: s += 40
    elif p["value"] > 1000000: s += 30
    elif p["value"] > 500000: s += 20

    if p.get("assessed_value") and p["value"] > p["assessed_value"] * 0.3:
        s += 15

    if p.get("land_use") and "Commercial" in str(p["land_use"]):
        s += 10

    if "review" in p["status"].lower():
        s += 15

    if "llc" in p["owner"].lower():
        s += 5

    return s


def classify(p):
    if p.get("assessed_value") and p["value"] > (p["assessed_value"] or 1) * 0.3:
        return "Capital Stack Stress Opportunity"

    if "review" in p["status"].lower():
        return "Timeline Leverage Arbitrage"

    if p.get("land_use") and "Commercial" in str(p["land_use"]):
        return "Supplier + GC Arbitrage"

    return "General Permit Arbitrage"


# ----------------------------
# ROUTES
# ----------------------------

@app.get("/")
def home():
    return render_template("dashboard.html")

@app.get("/api/permits")
def api_permits():
    return jsonify(fetch_permits())

@app.get("/export")
def export_csv():
    permits = fetch_permits()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["Permit","Owner","Address","Value","Assessed","Score","Deal Type"])

    for p in permits:
        cw.writerow([
            p.get("permit_id"),
            p.get("owner"),
            p.get("address"),
            p.get("value"),
            p.get("assessed_value"),
            p.get("score"),
            p.get("deal_type")
        ])

    output = si.getvalue()
    return Response(output, mimetype="text/csv",
        headers={"Content-Disposition":"attachment;filename=lead_sheet.csv"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
