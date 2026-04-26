from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class ProductRecord:
    image_url: str
    image_path: str
    product_title: str
    brand: str
    class_name: str
    gender: str
    sleeve: str
    product_url: str
    source: str = "myntra"


def load_existing_metadata(metadata_csv: Path) -> pd.DataFrame:
    if not metadata_csv.exists():
        return pd.DataFrame()
    return pd.read_csv(metadata_csv)


def existing_image_urls(metadata_csv: Path) -> set[str]:
    existing = load_existing_metadata(metadata_csv)
    if existing.empty or "image_url" not in existing.columns:
        return set()
    return set(existing["image_url"].dropna().astype(str))


def append_records(metadata_csv: Path, records: list[ProductRecord]) -> None:
    if not records:
        return

    metadata_csv.parent.mkdir(parents=True, exist_ok=True)
    new_frame = pd.DataFrame([asdict(record) for record in records])

    if metadata_csv.exists():
        old_frame = pd.read_csv(metadata_csv)
        combined = pd.concat([old_frame, new_frame], ignore_index=True)
        combined = combined.drop_duplicates(subset=["image_url"], keep="first")
    else:
        combined = new_frame

    combined.to_csv(metadata_csv, index=False)


def class_counts_by_name(metadata_csv: Path) -> dict[str, int]:
    existing = load_existing_metadata(metadata_csv)
    if existing.empty or "class_name" not in existing.columns:
        return {}
    grouped = existing.groupby("class_name").size()
    return {str(name): int(count) for name, count in grouped.items()}
