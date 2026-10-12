import os
import argparse
from pathlib import Path
from PIL import Image
import torch
import sys

# Add ai-agent to pythonpath
sys.path.append(str(Path(__file__).parent.parent.parent / "ai-agent"))
from inference import PatchCoreModel

def train(dataset_root: str, output_path: str, device: str = "cuda"):
    root_path = Path(dataset_root)
    screw_path = root_path / "screw" if (root_path / "screw").exists() else root_path
    train_good = screw_path / "train" / "good"

    if not train_good.exists():
        print(f"Error: {train_good} does not exist.")
        return False

    images = list(train_good.glob("*.png")) + list(train_good.glob("*.jpg"))
    if not images:
        print("Error: No training images found.")
        return False

    image_paths = [str(p) for p in images]
    print(f"Starting training on {len(image_paths)} images...")
    
    model = PatchCoreModel(backbone_name="resnet18", device=device)
    model.fit(image_paths)
    
    # Calibrated threshold based on training set distance (Good: ~4.9, Defect: ~8.9)
    model.threshold = 6.5
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    model.save_checkpoint(output_path)
    print("Training finished successfully.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=str, default="datasets/mvtec")
    parser.add_argument("--output", type=str, default="models/patchcore/screw_patchcore.pt")
    parser.add_argument("--device", type=str, default="cuda")
    args = parser.parse_args()
    train(args.data_root, args.output, args.device)
