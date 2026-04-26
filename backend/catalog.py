from __future__ import annotations

from pathlib import Path

import pandas as pd


def _to_asset_path(image_path: str) -> str | None:
    normalized = image_path.replace("\\", "/")
    prefix = "data/raw_images/"
    if normalized.startswith(prefix):
        return "/assets/" + normalized[len(prefix) :]
    return None


def list_products(
    metadata_csv: Path,
    *,
    limit: int = 100,
    offset: int = 0,
    class_name: str | None = None,
) -> list[dict]:
    if not metadata_csv.exists():
        return []

    frame = pd.read_csv(metadata_csv)
    if frame.empty:
        return []

    if class_name:
        frame = frame[frame["class_name"] == class_name]

    frame = frame.iloc[offset : offset + limit].copy()
    frame = frame.fillna("")

    products: list[dict] = []
    for _, row in frame.iterrows():
        image_path = str(row.get("image_path", ""))
        products.append(
            {
                "image_path": image_path,
                "image_web_path": _to_asset_path(image_path),
                "product_title": str(row.get("product_title", "")),
                "brand": str(row.get("brand", "")),
                "class_name": str(row.get("class_name", "")),
                "gender": str(row.get("gender", "")),
                "sleeve": str(row.get("sleeve", "")),
                "product_url": str(row.get("product_url", "")),
                "image_url": str(row.get("image_url", "")),
            }
        )
    return products
