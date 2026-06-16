"""
Quick smoke tests for the API using FastAPI's TestClient.
Run: python -m pytest test_api.py -v   (or `python test_api.py`)
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200


def test_list_customers():
    r = client.get("/api/customers")
    assert r.status_code == 200
    ids = [c["id"] for c in r.json()]
    assert "daystar" in ids
    assert "others" in ids


def test_breaker_options():
    r = client.get("/api/breakers/options")
    assert r.status_code == 200
    data = r.json()
    assert 36 in data["kA_ratings"]
    assert 250 in data["amperages"]


def test_breaker_lookup():
    r = client.get("/api/breakers/lookup?rating_kA=36&amperage=250")
    assert r.status_code == 200
    data = r.json()
    assert data["part_number"] == "MCCB-36K-250"
    assert data["cable_size"] == "95 mm²"


def test_breaker_lookup_invalid():
    r = client.get("/api/breakers/lookup?rating_kA=999&amperage=999")
    assert r.status_code == 404


def test_quotation_preview_daystar():
    payload = {
        "customer_id": "daystar",
        "project_name": "Test Project",
        "incomers": [{"quantity": 1, "rating_kA": 36, "amperage": 250}],
        "outgoings": [{"quantity": 4, "rating_kA": 25, "amperage": 100}],
    }
    r = client.post("/api/quotation/preview", json=payload)
    assert r.status_code == 200
    data = r.json()

    categories = [line["category"] for line in data["bom"]]
    assert "incomer" in categories
    assert "outgoing" in categories
    assert "accessory" in categories  # auto-included for Daystar

    # Daystar auto components
    descriptions = " ".join(line["description"] for line in data["bom"])
    assert "Emergency Stop" in descriptions
    assert "Shunt Trip" in descriptions
    assert "Power Meter" in descriptions
    assert "Cooling Fan" in descriptions
    assert "Filter" in descriptions

    assert data["grand_total"] > 0


def test_quotation_preview_others_no_optional():
    payload = {
        "customer_id": "others",
        "project_name": "Generic Project",
        "incomers": [{"quantity": 1, "rating_kA": 25, "amperage": 200}],
        "outgoings": [{"quantity": 2, "rating_kA": 10, "amperage": 100}],
    }
    r = client.post("/api/quotation/preview", json=payload)
    assert r.status_code == 200
    data = r.json()

    # No accessories should be present
    categories = [line["category"] for line in data["bom"]]
    assert "accessory" not in categories
    assert any("optional components were selected" in w for w in data["warnings"])


def test_quotation_preview_others_with_optional():
    payload = {
        "customer_id": "others",
        "project_name": "Generic Project With Extras",
        "incomers": [{"quantity": 1, "rating_kA": 25, "amperage": 200}],
        "outgoings": [{"quantity": 2, "rating_kA": 10, "amperage": 100}],
        "optional_components": {
            "e_stop": True, "e_stop_qty": 1,
            "meter": True, "meter_qty": 1,
            "fan": False, "fan_qty": 1,
            "shunt_trip": False, "shunt_trip_qty": 1,
            "filter": False, "filter_qty": 1,
        },
    }
    r = client.post("/api/quotation/preview", json=payload)
    assert r.status_code == 200
    data = r.json()
    accessory_pns = [line["part_number"] for line in data["bom"] if line["category"] == "accessory"]
    assert "ACC-ESTOP-001" in accessory_pns
    assert "ACC-MTR-DIG01" in accessory_pns


def test_quotation_invalid_breaker_combo():
    payload = {
        "customer_id": "daystar",
        "project_name": "Bad Combo",
        "incomers": [{"quantity": 1, "rating_kA": 999, "amperage": 999}],
        "outgoings": [{"quantity": 1, "rating_kA": 25, "amperage": 100}],
    }
    r = client.post("/api/quotation/preview", json=payload)
    assert r.status_code == 400


def test_export_excel():
    payload = {
        "customer_id": "daystar",
        "project_name": "Export Test",
        "incomers": [{"quantity": 1, "rating_kA": 36, "amperage": 250}],
        "outgoings": [{"quantity": 4, "rating_kA": 25, "amperage": 100}],
    }
    r = client.post("/api/quotation/export/excel", json=payload)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert len(r.content) > 1000


def test_export_spec():
    payload = {
        "customer_id": "daystar",
        "project_name": "Export Test",
        "incomers": [{"quantity": 1, "rating_kA": 36, "amperage": 250}],
        "outgoings": [{"quantity": 4, "rating_kA": 25, "amperage": 100}],
    }
    r = client.post("/api/quotation/export/spec", json=payload)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert len(r.content) > 1000


if __name__ == "__main__":
    import sys
    import traceback

    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed, failed = 0, 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except Exception:
            print(f"FAIL: {t.__name__}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
