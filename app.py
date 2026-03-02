import os
import requests
from flask import Flask, jsonify, render_template

app = Flask(__name__, static_folder="static", template_folder="templates")

BASE_URL = "https://services2.arcgis.com/CyVvlIiUfRBmMQuu/arcgis/rest/services/Building_Permits_Applications_view/FeatureServer"

# ----------------------------
# Find working layer
# ----------------------------
def find_layer():
    r = requests.get(f"{BASE_URL}?f=json", timeout=30)
    data = r.json()
    return [layer["id"] for layer in data.get("layers", [])]

# ----------------------------
# Fetch + Normalize
# ----------------------------
def fetch_permits(limit=50):
    layers = find_layer()

    for layer_id in layers:
        try:
            query_url = f"{BASE_URL}/{layer_id}/query"
            params = {
                "f": "json",
                "where": "1=1",
                "outFields": "*",
                "returnGeometry": "false",
                "resultRecordCount": str(limit)
            }

            r = requests.get(query_url, params=params, timeout=60)
            data = r.json()

            if not data.get("features"):
                continue

            results = []

            for f in data["features"]:
                attr = f.get("attributes", {})

                permit = {
                    "permit_id": safe_get(attr, ["PERMIT_NUMBER","APPLICATION_NUMBER","PERMITNO","OBJECTID"]),
                    "description": safe_get(attr, ["WORK_DESCRIPTION","DESCRIPTION","SCOPE_OF_WORK"]),
                    "status": safe_get(attr, ["STATUS","APPLICATION_STATUS","CURRENT_STATUS"]),
                    "value": safe_float(safe_get(attr, ["ESTIMATED_COST","VALUATION","JOB_COST"])),
                    "address": safe_get(attr, ["SITE_ADDRESS","ADDRESS","PROPERTY_ADDRESS"]),
                    "owner": safe_get(attr, ["OWNER_NAME","APPLICANT_NAME"])
                }

                permit["score"] = score(permit)
                permit["deal_type"] = classify(permit)

                results.append(permit)

            results.sort(key=lambda x: x["score"], reverse=True)
            return results

        except:
            continue

    return []

# ----------------------------
# Utilities
# ----------------------------
def safe_get(d, keys):
    for k in keys:
        if k in d and d[k]:
            return d[k]
    return ""

def safe_float(v):
    try:
        return float(v)
    except:
        return 0

# ----------------------------
# Scoring
# ----------------------------
def score(p):
    s = 0
    if p["value"] > 2000000: s += 40
    elif p["value"] > 1000000: s += 30
    elif p["value"] > 500000: s += 20

    if "review" in str(p["status"]).lower():
        s += 20

    if "llc" in str(p["owner"]).lower():
        s += 10

    keywords = ["hvac","sprinkler","restaurant","retail","warehouse"]
    for k in keywords:
        if k in str(p["description"]).lower():
            s += 5

    return s

def classify(p):
    if p["value"] > 1500000:
        return "Financing + Vendor Arbitrage"
    if "review" in str(p["status"]).lower():
        return "Timeline Leverage"
    return "Supplier / GC Arbitrage"

# ----------------------------
# Routes
# ----------------------------
@app.get("/")
def home():
    return render_template("dashboard.html")

@app.get("/api/permits")
def api_permits():
    return jsonify(fetch_permits())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
