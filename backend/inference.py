from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import requests
import torch
from PIL import Image
from torchvision.models import ResNet18_Weights

from backend.settings import PROJECT_ROOT
from training.model import MultiTaskResNet18

IDX_TO_GENDER = {0: "male", 1: "female"}
IDX_TO_SLEEVE = {0: "half_sleeve", 1: "full_sleeve"}


@dataclass(frozen=True)
class PredictionOutput:
    predicted_gender: str
    predicted_sleeve: str
    gender_confidence: float
    sleeve_confidence: float


class ModelPredictor:
    def __init__(self, checkpoint_path: Path):
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        self.checkpoint_path = checkpoint_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = MultiTaskResNet18(pretrained=False).to(self.device)
        self.transform = ResNet18_Weights.IMAGENET1K_V1.transforms()

        checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
        self.model.load_state_dict(checkpoint["state_dict"])
        self.model.eval()

        self.model_name = str(checkpoint.get("model_name", "multitask_resnet18"))
        timestamp = checkpoint.get("timestamp")
        if timestamp is None:
            modified = datetime.fromtimestamp(checkpoint_path.stat().st_mtime)
            timestamp = modified.isoformat(timespec="seconds")
        self.model_version = str(timestamp)

    def _is_http_url(self, image_reference: str) -> bool:
        parsed = urlparse(image_reference)
        return parsed.scheme in {"http", "https"}

    def load_image(self, image_reference: str) -> Image.Image:
        if self._is_http_url(image_reference):
            response = requests.get(image_reference, timeout=20)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert("RGB")

        raw_path = Path(image_reference)
        if not raw_path.is_absolute():
            raw_path = (PROJECT_ROOT / raw_path).resolve()
        if not raw_path.exists():
            raise FileNotFoundError(f"Image not found: {raw_path}")
        return Image.open(raw_path).convert("RGB")

    def predict(self, image_reference: str) -> PredictionOutput:
        image = self.load_image(image_reference)
        tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            output = self.model(tensor)
            gender_probs = torch.softmax(output["gender_logits"], dim=1).squeeze(0)
            sleeve_probs = torch.softmax(output["sleeve_logits"], dim=1).squeeze(0)

        gender_idx = int(torch.argmax(gender_probs).item())
        sleeve_idx = int(torch.argmax(sleeve_probs).item())
        return PredictionOutput(
            predicted_gender=IDX_TO_GENDER[gender_idx],
            predicted_sleeve=IDX_TO_SLEEVE[sleeve_idx],
            gender_confidence=float(gender_probs[gender_idx].item()),
            sleeve_confidence=float(sleeve_probs[sleeve_idx].item()),
        )
