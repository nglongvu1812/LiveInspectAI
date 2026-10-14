import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
import torchvision.transforms as transforms
import numpy as np
from PIL import Image
from sklearn.random_projection import SparseRandomProjection
from typing import Tuple, List, Optional
import io
import base64

class PatchCoreModel(nn.Module):
    """
    Self-contained PatchCore Model for Visual Anomaly Detection.
    Uses pretrained ResNet18 / WideResNet50 feature extractor.
    Extracts intermediate patch tokens from layer2 and layer3, builds memory bank of normal features.
    """
    def __init__(self, backbone_name: str = "resnet18", device: str = "cuda"):
        super().__init__()
        self.device = torch.device(device if (device == "cuda" and torch.cuda.is_available()) else "cpu")
        self.backbone_name = backbone_name
        
        # Load backbone
        if backbone_name == "resnet18":
            backbone = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        else:
            backbone = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
            
        self.conv1 = backbone.conv1
        self.bn1 = backbone.bn1
        self.relu = backbone.relu
        self.maxpool = backbone.maxpool
        self.layer1 = backbone.layer1
        self.layer2 = backbone.layer2
        self.layer3 = backbone.layer3
        
        for param in self.parameters():
            param.requires_grad = False
            
        self.to(self.device)
        self.eval()

        self.memory_bank: Optional[torch.Tensor] = None
        self.threshold: float = 0.5
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def extract_features(self, x: torch.Tensor) -> Tuple[torch.Tensor, Tuple[int, int]]:
        """
        Forward pass through backbone layers 2 and 3, concatenating patch tokens.
        """
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        l1 = self.layer1(x)
        l2 = self.layer2(l1)
        l3 = self.layer3(l2)

        # Upsample layer3 to layer2 resolution
        l3_upsampled = F.interpolate(l3, size=l2.shape[-2:], mode="bilinear", align_corners=False)
        
        # Concatenate features
        features = torch.cat([l2, l3_upsampled], dim=1) # [B, C2+C3, H, W]
        b, c, h, w = features.shape
        # Reshape to [B * H * W, C]
        features = features.permute(0, 2, 3, 1).reshape(-1, c)
        return features, (h, w)

    def fit(self, image_paths: List[str], subsample_ratio: float = 0.1):
        """
        Fit PatchCore memory bank on normal training images.
        """
        print(f"Fitting PatchCore on {len(image_paths)} normal images on device: {self.device}...")
        all_patch_features = []

        with torch.no_grad():
            for path in image_paths:
                img = Image.open(path).convert("RGB")
                tensor = self.transform(img).unsqueeze(0).to(self.device)
                patches, _ = self.extract_features(tensor)
                all_patch_features.append(patches.cpu())

        all_patch_features = torch.cat(all_patch_features, dim=0) # [Total_patches, Dim]
        print(f"Extracted {all_patch_features.shape[0]} total patch embeddings (Dim: {all_patch_features.shape[1]}).")

        # Subsample using coreset / random subsampling to fit in GPU VRAM
        n_subsample = int(all_patch_features.shape[0] * subsample_ratio)
        n_subsample = max(100, min(n_subsample, 10000)) # Keep bounded
        indices = torch.randperm(all_patch_features.shape[0])[:n_subsample]
        self.memory_bank = all_patch_features[indices].to(self.device)
        print(f"Memory bank saved with {self.memory_bank.shape[0]} patches on {self.device}.")

    def predict(self, pil_image: Image.Image) -> dict:
        """
        Run inference on a single PIL image.
        Returns anomaly_score, prediction, heatmap_base64.
        """
        if self.memory_bank is None:
            raise RuntimeError("Model has not been trained or loaded with a memory bank.")

        orig_w, orig_h = pil_image.size
        tensor = self.transform(pil_image.convert("RGB")).unsqueeze(0).to(self.device)

        with torch.no_grad():
            patches, (h, w) = self.extract_features(tensor)
            
            # Compute distance to nearest neighbor in memory bank for each patch
            # memory_bank: [N, D], patches: [P, D]
            # Use torch.cdist or cosine / euclidean
            dists = torch.cdist(patches, self.memory_bank, p=2) # [P, N]
            min_dists, _ = torch.min(dists, dim=1) # [P]
            
            # Max patch distance is image-level anomaly score
            raw_score = float(torch.max(min_dists).item())
            
            # Reshape patch distances to 2D anomaly map [H, W]
            anomaly_map = min_dists.reshape(h, w).cpu().numpy()
            
            # Normalize anomaly map to 0..255 for visualization
            map_min = float(anomaly_map.min())
            map_max = float(anomaly_map.max())
            if map_max > map_min:
                norm_map = (anomaly_map - map_min) / (map_max - map_min + 1e-8)
            else:
                norm_map = np.zeros_like(anomaly_map)

            # Resize heatmap to original image size using PIL
            heatmap_img = Image.fromarray((norm_map * 255).astype(np.uint8), mode="L")
            heatmap_img = heatmap_img.resize((orig_w, orig_h), resample=Image.Resampling.BILINEAR)

            # Apply colormap in PIL or save as grayscale heatmap PNG
            buffer = io.BytesIO()
            heatmap_img.save(buffer, format="PNG")
            heatmap_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # Determine prediction based on threshold
        prediction = "ANOMALY" if raw_score > self.threshold else "NORMAL"
        display_score = round(min(100.0, (raw_score / (self.threshold * 2.0)) * 100.0), 1)

        return {
            "prediction": prediction,
            "anomaly_score_raw": round(raw_score, 4),
            "display_score": display_score,
            "threshold": self.threshold,
            "heatmap_png_base64": heatmap_b64
        }

    def save_checkpoint(self, path: str):
        torch.save({
            "backbone_name": self.backbone_name,
            "memory_bank": self.memory_bank.cpu() if self.memory_bank is not None else None,
            "threshold": self.threshold
        }, path)
        print(f"Model saved to {path}")

    def load_checkpoint(self, path: str):
        data = torch.load(path, map_location=self.device)
        self.backbone_name = data["backbone_name"]
        self.threshold = data.get("threshold", 0.5)
        if data["memory_bank"] is not None:
            self.memory_bank = data["memory_bank"].to(self.device)
        print(f"Model loaded from {path} (Memory bank patches: {self.memory_bank.shape[0]}, Threshold: {self.threshold})")
