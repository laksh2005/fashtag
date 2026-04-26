from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_IMAGE_DIR = DATA_DIR / "raw_images"
METADATA_CSV = DATA_DIR / "metadata" / "metadata.csv"

MODELS_DIR = PROJECT_ROOT / "models"
CHECKPOINTS_DIR = MODELS_DIR / "checkpoints"
FINAL_METRICS_JSON = CHECKPOINTS_DIR / "final_metrics.json"
DEFAULT_CHECKPOINT = CHECKPOINTS_DIR / "best_multitask_resnet18.pt"

DATABASE_DIR = PROJECT_ROOT / "database"
PREDICTIONS_DB = DATABASE_DIR / "predictions.db"


def resolve_checkpoint_path() -> Path:
    if FINAL_METRICS_JSON.exists():
        try:
            metrics = json.loads(FINAL_METRICS_JSON.read_text(encoding="utf-8"))
            best_checkpoint = metrics.get("best_checkpoint")
            if best_checkpoint:
                checkpoint_path = Path(best_checkpoint)
                if checkpoint_path.exists():
                    return checkpoint_path
        except (json.JSONDecodeError, OSError):
            pass

    return DEFAULT_CHECKPOINT
