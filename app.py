import os
import requests
from flask import Flask, jsonify, render_template

app = Flask(__name__, static_folder="static", template_folder="templates")

# Cleveland ArcGIS public permit dataset
ARCGIS_URL = "https://services2.arcgis.com/CyVvlIiUfRBmMQuu/arcgis/rest/services/Building_Permits_Applications_view/FeatureServer/0/query"

def fetch_permits(limit=200):
    try:
        params = {
            "f": "json",
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "false",
            "resultRecordCount": str(limit)
        }

        r = requests.get(ARCGIS_URL, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()

    except Exception as e:
        return [{
            "permit_id": "ERROR",
            "description": str(e),
            "status": "API FAILURE",
            "value": 0
        }]

    rows = []

    for feature in data.get("features", []):
        p = feature.get("attributes", {})

        rows.append({
            "permit_id": p.get("PERMIT_NUMBER") or p.get("OBJECTID") or "N/A",
            "description": p.get("WORK_DESCRIPTION") or p.get("DESCRIPTION") or "",
            "status": p.get("STATUS") or "",
            "value": float(p.get("ESTIMATED_COST") or p.get("VALUATION") or 0)
        })

    return rows[:50]

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/crm")
def crm():
    return render_template("crm.html")

@app.get("/api/permits")
def api_permits():
    return jsonify(fetch_permits())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
