from __future__ import annotations

import torch.nn as nn
from torchvision.models import ResNet18_Weights, resnet18


class MultiTaskResNet18(nn.Module):
    def __init__(self, *, pretrained: bool = True):
        super().__init__()
        weights = ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
        backbone = resnet18(weights=weights)
        in_features = backbone.fc.in_features
        backbone.fc = nn.Identity()

        self.backbone = backbone
        self.gender_head = nn.Linear(in_features, 2)
        self.sleeve_head = nn.Linear(in_features, 2)

    def forward(self, images):
        features = self.backbone(images)
        gender_logits = self.gender_head(features)
        sleeve_logits = self.sleeve_head(features)
        return {"gender_logits": gender_logits, "sleeve_logits": sleeve_logits}
