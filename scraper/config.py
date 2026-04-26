from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_IMAGE_DIR = DATA_DIR / "raw_images"
METADATA_DIR = DATA_DIR / "metadata"
METADATA_CSV = METADATA_DIR / "metadata.csv"


@dataclass(frozen=True)
class ScrapeTarget:
    class_name: str
    gender: str
    sleeve: str
    search_queries: tuple[str, ...]

    @property
    def image_dir(self) -> Path:
        return RAW_IMAGE_DIR / self.class_name


SCRAPE_TARGETS: tuple[ScrapeTarget, ...] = (
    ScrapeTarget(
        class_name="male_full",
        gender="male",
        sleeve="full_sleeve",
        search_queries=(
            "men full sleeve shirts",
            "men formal full sleeve shirts",
            "men casual full sleeve shirts",
            "men full sleeve t shirts",
        ),
    ),
    ScrapeTarget(
        class_name="male_half",
        gender="male",
        sleeve="half_sleeve",
        search_queries=(
            "men half sleeve t shirts",
            "men half sleeve shirts",
            "men short sleeve t shirts",
            "men polo t shirts",
        ),
    ),
    ScrapeTarget(
        class_name="female_full",
        gender="female",
        sleeve="full_sleeve",
        search_queries=(
            "women full sleeve tops",
            "women full sleeve tshirts",
            "women full sleeve kurtas",
            "women full sleeve shirts",
        ),
    ),
    ScrapeTarget(
        class_name="female_half",
        gender="female",
        sleeve="half_sleeve",
        search_queries=(
            "women half sleeve tops",
            "women short sleeve tops",
            "women half sleeve tshirts",
            "women short sleeve shirts",
        ),
    ),
)


BASE_URL = "https://www.myntra.com"
SEARCH_URL_TEMPLATE = BASE_URL + "/{query}"

DEFAULT_TARGET_PER_CLASS = 250
DEFAULT_SCROLL_ROUNDS = 12
DEFAULT_MAX_PAGES_PER_QUERY = 20
DEFAULT_REQUEST_TIMEOUT_SECONDS = 20
DEFAULT_DELAY_SECONDS = 2.0
DEFAULT_DOWNLOAD_DELAY_SECONDS = 0.25
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def ensure_data_directories() -> None:
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    for target in SCRAPE_TARGETS:
        target.image_dir.mkdir(parents=True, exist_ok=True)
