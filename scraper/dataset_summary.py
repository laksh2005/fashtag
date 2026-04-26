from __future__ import annotations

import argparse
from pathlib import Path

from scraper.config import METADATA_CSV, RAW_IMAGE_DIR, SCRAPE_TARGETS
from scraper.metadata_builder import class_counts_by_name

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def image_count_in_dir(folder: Path) -> int:
    if not folder.exists():
        return 0
    return sum(1 for path in folder.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show dataset counts for FashTag.")
    parser.add_argument(
        "--metadata-csv",
        type=Path,
        default=METADATA_CSV,
        help="Path to metadata.csv",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metadata_counts = class_counts_by_name(args.metadata_csv)

    header = (
        f"{'Class':<14} {'Metadata Count':>14} {'Image Files':>12} "
        f"{'Gender':>10} {'Sleeve':>12}"
    )
    print(header)
    print("-" * len(header))

    total_metadata = 0
    total_files = 0
    for target in SCRAPE_TARGETS:
        class_name = target.class_name
        metadata_count = metadata_counts.get(class_name, 0)
        image_files = image_count_in_dir(RAW_IMAGE_DIR / class_name)
        total_metadata += metadata_count
        total_files += image_files
        print(
            f"{class_name:<14} {metadata_count:>14} {image_files:>12} "
            f"{target.gender:>10} {target.sleeve:>12}"
        )

    print("-" * len(header))
    print(f"{'TOTAL':<14} {total_metadata:>14} {total_files:>12}")
    print(f"Metadata CSV: {args.metadata_csv}")
    print(f"Image root:   {RAW_IMAGE_DIR}")


if __name__ == "__main__":
    main()
