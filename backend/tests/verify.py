"""
IntelliPlant — Full System Verification
Run: python verify.py
"""

import httpx
import sys
import time

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0

def test(name, method="GET", path="/", expected=200, data=None):
    global PASS, FAIL
    url = f"{BASE}{path}"
    try:
        if method == "GET":
            r = httpx.get(url, timeout=10)
        else:
            r = httpx.post(url, json=data, timeout=10)
        status = "PASS" if r.status_code == expected else f"FAIL (got {r.status_code})"
        if status == "PASS":
            PASS += 1
        else:
            FAIL += 1
        print(f"  [{status}] {method} {path}")
        return r
    except Exception as e:
        FAIL += 1
        print(f"  [FAIL] {method} {path} — {e}")
        return None

def main():
    global PASS, FAIL
    PASS = 0
    FAIL = 0

    print("\n" + "=" * 50)
    print("  IntelliPlant — Full System Verification")
    print("=" * 50 + "\n")

    # 1. Health
    print("\n--- Core ---")
    test("Health", "GET", "/health")
    test("Dashboard KPIs", "GET", "/api/dashboard/kpis")
    test("Heatmap Live", "GET", "/api/heatmap/live")
    test("Incidents List", "GET", "/api/incidents")
    test("Permits List", "GET", "/api/permits")
    test("Emergency Active", "GET", "/api/emergency/active")
    test("Compliance Score", "GET", "/api/audits/compliance-score")

    # 2. CCTV
    print("\n--- CCTV / Computer Vision ---")
    test("CCTV Summary", "GET", "/api/cctv/summary")
    test("CCTV Alerts", "GET", "/api/cctv/alerts")
    test("CCTV Heatmap", "GET", "/api/cctv/heatmap")
    test("CCTV Process", "POST", "/api/cctv/process")

    # 3. IoT
    print("\n--- IoT / SCADA ---")
    test("IoT Metrics", "GET", "/api/iot/metrics")
    test("IoT Devices", "GET", "/api/iot/devices")
    test("IoT Recent", "GET", "/api/iot/recent")
    test("IoT Stream", "POST", "/api/iot/stream")

    # 4. Knowledge Graph
    print("\n--- Knowledge Graph ---")
    test("KG Stats", "GET", "/api/knowledge-graph/stats")
    test("KG Data", "GET", "/api/knowledge-graph/data")
    test("KG Risk Propagation", "GET", "/api/knowledge-graph/risk-propagation")

    # 5. Orchestrator
    print("\n--- Orchestrator ---")
    test("Orch Status", "GET", "/api/orchestrator/status")
    test("Orch Agents", "GET", "/api/orchestrator/agents")
    test("Orch Decisions", "GET", "/api/orchestrator/decisions")

    # Summary
    total = PASS + FAIL
    print(f"\n{'=' * 50}")
    print(f"  RESULTS:  {PASS}/{total} passed  |  {FAIL} failed")
    print(f"{'=' * 50}\n")

    return PASS == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
