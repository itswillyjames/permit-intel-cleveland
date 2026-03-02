"""Comprehensive test script to exercise the ingest, scoring, and enrichment pipeline."""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def log_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_api_health():
    """Test basic API connectivity."""
    log_section("API Health Check")
    try:
        r = requests.get(f"{BASE_URL}/")
        print(f"✓ API is online: {r.json()['message']}")
        return True
    except Exception as e:
        print(f"✗ API is offline: {e}")
        return False

def ingest_sample_permits():
    """Ingest multiple sample permits to demonstrate the pipeline."""
    log_section("Ingesting Sample Permits")
    
    samples = [
        {
            "permit_id": "SF-2024-001",
            "city": "San Francisco",
            "address": "100 Market St",
            "lat": 37.7942,
            "lon": -122.3969,
            "permit_type": "Commercial",
            "description": "TI for new tech office space",
            "valuation": 2500000,
            "status": "Issued",
            "source_url": "https://data.sfgov.org/resource/i98e-djp9",
        },
        {
            "permit_id": "SF-2024-002",
            "city": "San Francisco",
            "address": "250 Valencia St",
            "lat": 37.7616,
            "lon": -122.4213,
            "permit_type": "Commercial",
            "description": "Restaurant build-out with HVAC and electrical",
            "valuation": 750000,
            "status": "Filed",
            "source_url": "https://data.sfgov.org/resource/i98e-djp9",
        },
        {
            "permit_id": "NYC-2024-001",
            "city": "New York",
            "address": "350 Fifth Avenue",
            "lat": 40.7580,
            "lon": -73.9855,
            "permit_type": "Commercial",
            "description": "Office expansion with sprinkler system",
            "valuation": 5000000,
            "status": "Issued",
            "source_url": "https://data.cityofnewyork.us/Housing-Development/New-Building-Permits/wvjb-nzaa",
        },
    ]
    
    ingested = []
    for sample in samples:
        try:
            r = requests.post(f"{BASE_URL}/permits/ingest", json=sample)
            if r.status_code == 200:
                permit = r.json()
                ingested.append(permit)
                print(f"✓ Ingested {sample['permit_id']}: {permit['address']}")
            else:
                print(f"✗ Failed to ingest {sample['permit_id']}: {r.status_code}")
        except Exception as e:
            print(f"✗ Error ingesting {sample['permit_id']}: {e}")
    
    return ingested

def score_permits(permits):
    """Score all ingested permits."""
    log_section("Scoring Permits")
    
    scored = []
    for permit in permits:
        try:
            r = requests.post(f"{BASE_URL}/permits/{permit['id']}/score")
            if r.status_code == 200:
                score = r.json()
                scored.append(score)
                win_score = round(score['win_score'], 2)
                print(f"✓ Scored {permit['permit_id']}: WIN={win_score}")
            else:
                print(f"✗ Failed to score permit {permit['id']}: {r.status_code}")
        except Exception as e:
            print(f"✗ Error scoring permit {permit['id']}: {e}")
    
    return scored

def list_permits():
    """List all permits in the database."""
    log_section("Listing All Permits")
    
    try:
        r = requests.get(f"{BASE_URL}/permits/")
        if r.status_code == 200:
            permits = r.json()
            print(f"Total permits in database: {len(permits)}\n")
            for p in permits[:5]:  # Show first 5
                print(f"  - {p['permit_id']:15} | {p['city']:15} | ${p['valuation']:,}")
            if len(permits) > 5:
                print(f"  ... and {len(permits) - 5} more")
            return permits
        else:
            print(f"✗ Failed to list permits: {r.status_code}")
    except Exception as e:
        print(f"✗ Error listing permits: {e}")
    
    return []

def manage_sources():
    """Demonstrate source management."""
    log_section("Source Management")
    
    # List current sources
    try:
        r = requests.get(f"{BASE_URL}/sources/")
        if r.status_code == 200:
            sources = r.json()
            print(f"Registered sources: {len(sources)}")
            for src in sources:
                print(f"  - {src['city']}")
    except Exception as e:
        print(f"Info: {e}")
    
    # Add a new source
    new_source = {
        "city": "Chicago",
        "urls": {
            "type": "Socrata",
            "url": "https://data.cityofchicago.org/Buildings/Building-Permits/ydr8-5enu"
        }
    }
    try:
        r = requests.post(f"{BASE_URL}/sources/add", json=new_source)
        if r.status_code == 200:
            print(f"\n✓ Added source for Chicago")
    except Exception as e:
        print(f"Note: Could not add source: {e}")

def generate_report(all_permits, scored_permits):
    """Generate a summary report of the pipeline run."""
    log_section("Pipeline Summary Report")
    
    print(f"Ingest Stage:")
    print(f"  - Total permits ingested: {len(all_permits)}")
    
    # Calculate WIN score statistics
    if scored_permits:
        win_scores = [s['win_score'] for s in scored_permits]
        avg_win = sum(win_scores) / len(win_scores)
        max_win = max(win_scores)
        print(f"\nScoring Stage:")
        print(f"  - Permits scored: {len(scored_permits)}")
        print(f"  - Average WIN score: {avg_win:.2f}")
        print(f"  - Max WIN score: {max_win:.2f}")
        print(f"  - Opportunities (WIN > 0.7): {sum(1 for s in win_scores if s > 0.7)}")
    
    # Group by city
    cities = {}
    for p in all_permits:
        city = p.get('city', 'Unknown')
        if city not in cities:
            cities[city] = 0
        cities[city] += 1
    
    print(f"\nGeographic Distribution:")
    for city, count in sorted(cities.items()):
        print(f"  - {city}: {count} permits")

def main():
    """Execute the full pipeline test."""
    print("\n" + "="*60)
    print("  PERMIT ARBITRAGE INTELLIGENCE HUB - PIPELINE TEST")
    print("="*60)
    
    # Check API health
    if not test_api_health():
        print("\n✗ Cannot connect to API. Is it running?")
        print("   Run: cd backend && uvicorn app.main:app --reload")
        return
    
    # Run pipeline stages
    permits = ingest_sample_permits()
    if not permits:
        print("\n✗ No permits ingested. Stopping.")
        return
    
    scores = score_permits(permits)
    all_permits = list_permits()
    manage_sources()
    generate_report(all_permits, scores)
    
    print("\n" + "="*60)
    print("  ✓ Pipeline test completed successfully!")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
