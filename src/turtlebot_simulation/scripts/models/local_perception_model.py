"""Minimal PyTorch model skeleton for local perception."""

from typing import Any, Dict


def build_model(cfg: Dict[str, Any]):
    """Build a small fusion model using image and IMU inputs."""
    import torch
    import torch.nn as nn

    model_cfg = cfg.get("model", {}) if isinstance(cfg, dict) else {}
    img_channels = int(model_cfg.get("image_channels", 3))
    imu_dim = int(model_cfg.get("imu_dim", 10))
    hidden_dim = int(model_cfg.get("hidden_dim", 64))

    class LocalFusionModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.cnn = nn.Sequential(
                nn.Conv2d(img_channels, 16, kernel_size=3, stride=2, padding=1),
                nn.ReLU(inplace=True),
                nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1),
                nn.ReLU(inplace=True),
                nn.AdaptiveAvgPool2d((1, 1)),
            )
            self.head = nn.Sequential(
                nn.Linear(32 + imu_dim, hidden_dim),
                nn.ReLU(inplace=True),
                nn.Linear(hidden_dim, 1),
            )

        def forward(self, image: torch.Tensor, imu: torch.Tensor) -> torch.Tensor:
            feats = self.cnn(image).flatten(1)
            fused = torch.cat([feats, imu], dim=1)
            return self.head(fused)

    return LocalFusionModel()
