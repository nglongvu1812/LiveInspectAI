import os
import sys
import argparse
from pathlib import Path
from PIL import Image

REQUIRED_SPLITS = ["train", "test"]
REQUIRED_TRAIN_SUBDIRS = ["good"]

def validate_mvtec_screw(dataset_root: str):
    root_path = Path(dataset_root)
    print(f"Validating MVTec AD category 'screw' at: {root_path.resolve()}")
    
    if not root_path.exists():
        print(f"ERROR: Dataset root directory does not exist: {root_path}")
        return False
        
    screw_path = root_path / "screw" if (root_path / "screw").exists() else root_path

    # Check train directory
    train_good = screw_path / "train" / "good"
    if not train_good.exists():
        print(f"ERROR: Missing train/good directory at {train_good}")
        return False

    train_images = list(train_good.glob("*.png")) + list(train_good.glob("*.jpg"))
    print(f"[OK] Found {len(train_images)} normal training images in {train_good}")
    if len(train_images) == 0:
        print("ERROR: train/good directory contains 0 images.")
        return False

    # Check test directory
    test_dir = screw_path / "test"
    if not test_dir.exists():
        print(f"ERROR: Missing test directory at {test_dir}")
        return False

    test_categories = [d.name for d in test_dir.iterdir() if d.is_dir()]
    print(f"[OK] Found test defect categories: {test_categories}")

    # Check image readability and dimensions
    sample_img = Image.open(train_images[0])
    print(f"[OK] Sample image size: {sample_img.size}, format: {sample_img.format}, mode: {sample_img.mode}")

    print("All dataset checks passed successfully.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate MVTec AD dataset directory structure")
    parser.add_argument("--data-root", type=str, default="datasets/mvtec", help="Path to MVTec AD dataset root")
    args = parser.parse_args()
    success = validate_mvtec_screw(args.data_root)
    sys.exit(0 if success else 1)
