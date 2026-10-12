import argparse
from pathlib import Path
from PIL import Image
import json
import time
import sys

sys.path.append(str(Path(__file__).parent.parent.parent / "ai-agent"))
from inference import PatchCoreModel

def evaluate(model_path: str, data_root: str, device: str = "cuda"):
    model = PatchCoreModel(device=device)
    model.load_checkpoint(model_path)

    screw_path = Path(data_root) / "screw" if (Path(data_root) / "screw").exists() else Path(data_root)
    test_dir = screw_path / "test"

    results = []
    latencies = []

    for category_dir in test_dir.iterdir():
        if not category_dir.is_dir():
            continue
        is_anomaly = category_dir.name != "good"
        for img_path in list(category_dir.glob("*.png")) + list(category_dir.glob("*.jpg")):
            img = Image.open(img_path)
            start_t = time.perf_counter()
            pred = model.predict(img)
            lat_ms = (time.perf_counter() - start_t) * 1000.0
            latencies.append(lat_ms)

            results.append({
                "file": img_path.name,
                "category": category_dir.name,
                "ground_truth": "ANOMALY" if is_anomaly else "NORMAL",
                "predicted": pred["prediction"],
                "raw_score": pred["anomaly_score_raw"],
                "threshold": pred["threshold"],
                "latency_ms": round(lat_ms, 2)
            })

    # Summary
    correct = sum(1 for r in results if r["ground_truth"] == r["predicted"])
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    report = {
        "model_path": model_path,
        "device": device,
        "total_evaluated": len(results),
        "accuracy": round(correct / len(results) if results else 0, 4),
        "average_latency_ms": round(avg_latency, 2),
        "details": results
    }

    report_path = "models/patchcore/eval_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Evaluation complete: {correct}/{len(results)} correct (Avg latency: {avg_latency:.2f} ms).")
    print(f"Report saved to {report_path}")
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, default="models/patchcore/screw_patchcore.pt")
    parser.add_argument("--data-root", type=str, default="datasets/mvtec")
    parser.add_argument("--device", type=str, default="cuda")
    args = parser.parse_args()
    evaluate(args.model_path, args.data_root, args.device)
