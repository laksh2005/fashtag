from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import torch
from PIL import Image
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset

GENDER_TO_INDEX = {"male": 0, "female": 1}
SLEEVE_TO_INDEX = {"half_sleeve": 0, "full_sleeve": 1}


@dataclass(frozen=True)
class SplitFrames:
    train: pd.DataFrame
    val: pd.DataFrame


def load_clean_metadata(metadata_csv: Path, project_root: Path) -> pd.DataFrame:
    frame = pd.read_csv(metadata_csv)
    required_cols = {"image_path", "gender", "sleeve", "class_name"}
    missing = required_cols.difference(frame.columns)
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise ValueError(f"metadata.csv missing required columns: {missing_str}")

    frame = frame.copy()
    frame["gender"] = frame["gender"].astype(str).str.strip().str.lower()
    frame["sleeve"] = frame["sleeve"].astype(str).str.strip().str.lower()
    frame["image_path"] = frame["image_path"].astype(str).str.strip()
    frame["absolute_image_path"] = frame["image_path"].apply(lambda rel: str((project_root / rel).resolve()))

    frame = frame[frame["gender"].isin(GENDER_TO_INDEX)]
    frame = frame[frame["sleeve"].isin(SLEEVE_TO_INDEX)]
    frame = frame.drop_duplicates(subset=["image_path"], keep="first")
    frame = frame[frame["absolute_image_path"].apply(lambda p: Path(p).exists())]
    frame = frame.reset_index(drop=True)
    return frame


def build_train_val_split(
    frame: pd.DataFrame,
    *,
    val_size: float,
    seed: int,
) -> SplitFrames:
    if frame.empty:
        raise ValueError("No rows available for training after metadata filtering.")
    if len(frame) < 8:
        raise ValueError("Dataset is too small; collect more images before training.")

    stratify_column = frame["class_name"].astype(str)
    train_frame, val_frame = train_test_split(
        frame,
        test_size=val_size,
        random_state=seed,
        stratify=stratify_column,
    )
    return SplitFrames(train=train_frame.reset_index(drop=True), val=val_frame.reset_index(drop=True))


class FashionMultiTaskDataset(Dataset):
    def __init__(self, frame: pd.DataFrame, transform=None):
        self.frame = frame.reset_index(drop=True)
        self.transform = transform

    def __len__(self) -> int:
        return len(self.frame)

    def __getitem__(self, index: int):
        row = self.frame.iloc[index]
        image = Image.open(row["absolute_image_path"]).convert("RGB")
        if self.transform is not None:
            image = self.transform(image)

        gender_idx = GENDER_TO_INDEX[row["gender"]]
        sleeve_idx = SLEEVE_TO_INDEX[row["sleeve"]]
        target = {
            "gender": torch.tensor(gender_idx, dtype=torch.long),
            "sleeve": torch.tensor(sleeve_idx, dtype=torch.long),
        }
        return image, target
