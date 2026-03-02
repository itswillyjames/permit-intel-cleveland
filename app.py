import os
import json
import logging
from datetime import datetime, timedelta, timezone
import requests
from flask import Flask, jsonify, request, render_template

logging.basicConfig(level=logging.INFO)
app = Flask(__name__, static_folder="static", template_folder="templates")

ARCGIS_URL = "https://services2.arcgis.com/CyVvlIiUfRBmMQuu/arcgis/rest/services/Building_Permits_Applications_view/FeatureServer/0/query"

def now_utc():
    return datetime.now(timezone.utc)

def fetch_permits(days=60, min_val=500000, limit=2000):
    params = {
        "f":"json",
        "where":"1=1",
        "outFields":"*",
        "returnGeometry":"false",
        "resultRecordCount": str(limit)
    }
    r = requests.get(ARCGIS_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    rows = []
    for f in data.get("features", []):
        p = f.get("attributes", {})
        val = float(p.get("ESTIMATED_COST") or 0)
        if val >= min_val:
            rows.append({
                "permit_id": p.get("PERMIT_NUMBER") or p.get("OBJECTID"),
                "description": p.get("WORK_DESCRIPTION",""),
                "status": p.get("STATUS",""),
                "value": val
            })
    rows.sort(key=lambda x: x["value"], reverse=True)
    return rows[:50]

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/crm")
def crm():
    return render_template("crm.html")

@app.get("/api/permits")
def api_permits():
    rows = fetch_permits()
    return jsonify(rows)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
