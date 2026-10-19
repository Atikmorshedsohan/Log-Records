import json
import sys
import os

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    print("\n--- 1. Testing GET / (Root & Service Status) ---")
    response = client.get("/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200


def test_health():
    print("\n--- 2. Testing GET /health ---")
    response = client.get("/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_collect_logs():
    print("\n--- 3. Testing POST /api/logs ---")
    sample_payload = [
        {
            "timestamp": "2026-10-19T09:30:00Z",
            "host": "WORKSTATION-01",
            "source": "fluent-bit-test",
            "level": "INFO",
            "message": "Fluent Bit simulated log collector test event"
        }
    ]
    response = client.post("/api/logs", json=sample_payload)
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception:
        print(f"Response text: {response.text}")


def test_ingest_json_lines():
    print("\n--- 4. Testing POST /ingest (json_lines / NDJSON + X-Collector-Token) ---")
    ndjson_data = (
        '{"os_type":"windows","hostname":"my-windows-pc","event":"4624","Channel":"Security"}\n'
        '{"os_type":"windows","hostname":"my-windows-pc","event":"7036","Channel":"System"}\n'
    )
    headers = {
        "Content-Type": "application/x-ndjson",
        "X-Collector-Token": "YOUR_COLLECTOR_TOKEN",
    }
    response = client.post("/ingest", content=ndjson_data, headers=headers)
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception:
        print(f"Response text: {response.text}")


if __name__ == "__main__":
    print("=" * 50)
    print("Running Automated API Tests for Log Collector")
    print("=" * 50)
    test_root()
    test_health()
    test_collect_logs()
    test_ingest_json_lines()
    print("\n" + "=" * 50)
    print("Test Execution Finished!")
    print("=" * 50)
