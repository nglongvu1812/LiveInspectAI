import pytest
import torch
from PIL import Image
from inference import PatchCoreModel

def test_patchcore_model_forward():
    model = PatchCoreModel(device="cpu")
    # Test random input image
    img = Image.new("RGB", (256, 256), color=(100, 100, 100))
    tensor = model.transform(img).unsqueeze(0).to(model.device)
    patches, (h, w) = model.extract_features(tensor)
    
    assert patches.shape[0] == h * w
    assert patches.shape[1] == 384  # ResNet18 layer2 (128) + layer3 (256)
    assert h == 28
    assert w == 28

def test_patchcore_predict_with_weights():
    from pathlib import Path
    model_path = Path(__file__).parent.parent.parent / "models" / "patchcore" / "screw_patchcore.pt"
    model = PatchCoreModel(device="cuda" if torch.cuda.is_available() else "cpu")
    model.load_checkpoint(str(model_path))
    
    img = Image.new("RGB", (256, 256), color=(40, 42, 45))
    res = model.predict(img)
    
    assert res["prediction"] in ["NORMAL", "ANOMALY"]
    assert isinstance(res["anomaly_score_raw"], float)
    assert res["threshold"] == 6.5
    assert len(res["heatmap_png_base64"]) > 50
