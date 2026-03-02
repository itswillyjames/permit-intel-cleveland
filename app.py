import os
import requests
from flask import Flask, jsonify, render_template

app = Flask(__name__, static_folder="static", template_folder="templates")

BASE_URL = "https://services2.arcgis.com/CyVvlIiUfRBmMQuu/arcgis/rest/services/Building_Permits_Applications_view/FeatureServer"

def find_working_layer():
    try:
        r = requests.get(f"{BASE_URL}?f=json", timeout=30)
        data = r.json()
        layers = data.get("layers", [])
        return [layer["id"] for layer in layers]
    except:
        return []

def fetch_permits(limit=50):
    layers = find_working_layer()

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

            if data.get("features"):
                results = []
                for f in data["features"]:
                    results.append(f["attributes"])
                return results[:50]

        except:
            continue

    return [{"error": "No working layer found"}]

@app.get("/")
def home():
    return render_template("dashboard.html")

@app.get("/api/permits")
def api_permits():
    return jsonify(fetch_permits())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
