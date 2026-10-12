import asyncio
import base64
import io
import time
from pathlib import Path
from PIL import Image
import httpx

API_BASE = "http://127.0.0.1:8000"

async def run_smoke_test():
    print("=" * 60)
    print("LiveInspectAI End-to-End Smoke Test")
    print("=" * 60)

    async with httpx.AsyncClient(base_url=API_BASE, timeout=30.0) as client:
        # 1. Health check
        res = await client.get("/healthz")
        assert res.status_code == 200, f"Healthz failed: {res.text}"
        print("[PASS] 1. Backend /healthz is OK")

        # 2. Check Agent Status
        status_res = await client.get("/api/v1/status")
        assert status_res.status_code == 200, f"Status failed: {status_res.text}"
        status_data = status_res.json()
        print(f"[INFO] 2. Agent Status: online={status_data['online']}, device={status_data.get('hardware_device')}")
        assert status_data["online"] is True, "Smoke test expects AI Agent to be connected and online!"

        # 3. Test Normal Image Inference
        test_normal_path = Path("datasets/mvtec/screw/test/good/screw_test_good_000.png")
        if not test_normal_path.exists():
            print(f"[FAIL] Missing test image at {test_normal_path}")
            return False

        with open(test_normal_path, "rb") as f:
            files = {"file": ("normal_screw.png", f.read(), "image/png")}
            t0 = time.perf_counter()
            infer_res = await client.post("/api/v1/inferences", files=files)
            lat = (time.perf_counter() - t0) * 1000

        assert infer_res.status_code == 200, f"Inference failed: {infer_res.text}"
        data = infer_res.json()
        print(f"[PASS] 3. Normal sample inference: Prediction={data['prediction']}, Score={data['anomaly_score_raw']}, Latency={data['inference_ms']}ms (Total HTTP={lat:.1f}ms)")
        assert data["prediction"] == "NORMAL", f"Expected NORMAL but got {data['prediction']}"
        assert data["heatmap_png_base64"] is not None, "Expected base64 heatmap"

        # 4. Test Defect Image Inference
        test_defect_path = Path("datasets/mvtec/screw/test/thread_damage/screw_defect_000.png")
        with open(test_defect_path, "rb") as f:
            files = {"file": ("defect_screw.png", f.read(), "image/png")}
            infer_defect_res = await client.post("/api/v1/inferences", files=files)

        assert infer_defect_res.status_code == 200, f"Defect inference failed: {infer_defect_res.text}"
        defect_data = infer_defect_res.json()
        print(f"[PASS] 4. Defect sample inference: Prediction={defect_data['prediction']}, Score={defect_data['anomaly_score_raw']}, Latency={defect_data['inference_ms']}ms")
        assert defect_data["prediction"] == "ANOMALY", f"Expected ANOMALY but got {defect_data['prediction']}"

        # 5. Check History List & CSV Export
        hist_res = await client.get("/api/v1/inspections")
        assert hist_res.status_code == 200
        hist_data = hist_res.json()
        print(f"[PASS] 5. History records count: {hist_data['total']}")
        assert hist_data["total"] >= 2

        csv_res = await client.get("/api/v1/inspections/export.csv")
        assert csv_res.status_code == 200
        assert "Prediction" in csv_res.text
        print("[PASS] 6. Export CSV verified successfully.")

    print("=" * 60)
    print("ALL SMOKE TESTS PASSED - END-TO-END PIPELINE VERIFIED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
