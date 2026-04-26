from __future__ import annotations

import argparse
import random
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl, quote_plus, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options

from scraper.config import (
    BASE_URL,
    DEFAULT_DELAY_SECONDS,
    DEFAULT_MAX_PAGES_PER_QUERY,
    DEFAULT_SCROLL_ROUNDS,
    DEFAULT_TARGET_PER_CLASS,
    METADATA_CSV,
    PROJECT_ROOT,
    SCRAPE_TARGETS,
    SEARCH_URL_TEMPLATE,
    USER_AGENT,
    ScrapeTarget,
    ensure_data_directories,
)
from scraper.image_downloader import ImageDownloadError, download_image
from scraper.metadata_builder import (
    ProductRecord,
    append_records,
    class_counts_by_name,
    existing_image_urls,
)


@dataclass(frozen=True)
class ProductCandidate:
    image_url: str
    product_title: str
    brand: str
    product_url: str


def build_driver(headless: bool) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1440,1200")
    options.add_argument(f"--user-agent={USER_AGENT}")
    return webdriver.Chrome(options=options)


def search_url_for(query: str) -> str:
    return SEARCH_URL_TEMPLATE.format(query=quote_plus(query).replace("+", "-"))


def with_page(url: str, page_number: int) -> str:
    split = urlsplit(url)
    query_params = dict(parse_qsl(split.query, keep_blank_values=True))
    query_params["p"] = str(page_number)
    return urlunsplit((split.scheme, split.netloc, split.path, urlencode(query_params), split.fragment))


def scroll_results(driver: webdriver.Chrome, rounds: int, delay_seconds: float) -> None:
    last_height = 0
    for _ in range(rounds):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(delay_seconds + random.uniform(0.2, 0.8))
        height = driver.execute_script("return document.body.scrollHeight")
        if height == last_height:
            break
        last_height = height


def _candidate_from_card(card) -> ProductCandidate | None:
    image = card.select_one("img")
    link = card.select_one("a[href]")

    image_url = ""
    if image:
        image_url = (
            image.get("src")
            or image.get("data-src")
            or image.get("data-original")
            or image.get("data-image-url")
            or ""
        )

    if not image_url:
        style = card.get("style", "")
        marker = "url("
        if marker in style:
            image_url = style.split(marker, 1)[1].split(")", 1)[0].strip("'\"")

    if not image_url:
        return None

    brand_node = card.select_one(".product-brand")
    title_node = card.select_one(".product-product")
    fallback_title = image.get("alt", "") if image else ""

    brand = brand_node.get_text(" ", strip=True) if brand_node else ""
    title = title_node.get_text(" ", strip=True) if title_node else fallback_title
    href = link.get("href") if link else ""

    return ProductCandidate(
        image_url=image_url,
        product_title=title or fallback_title or "Unknown product",
        brand=brand,
        product_url=urljoin(BASE_URL, href),
    )


def parse_products(html: str) -> list[ProductCandidate]:
    soup = BeautifulSoup(html, "html.parser")

    cards = soup.select("li.product-base")
    if not cards:
        cards = soup.select("[class*='product-base'], [class*='Product']")

    candidates: list[ProductCandidate] = []
    seen_urls: set[str] = set()
    for card in cards:
        candidate = _candidate_from_card(card)
        if candidate and candidate.image_url not in seen_urls:
            seen_urls.add(candidate.image_url)
            candidates.append(candidate)
    return candidates


def scrape_target(
    driver: webdriver.Chrome,
    target: ScrapeTarget,
    *,
    target_per_class: int,
    already_in_metadata: int,
    known_image_urls: set[str],
    scroll_rounds: int,
    delay_seconds: float,
    max_pages_per_query: int,
) -> list[ProductRecord]:
    records: list[ProductRecord] = []
    current_total = already_in_metadata
    if current_total >= target_per_class:
        print(f"\n{target.class_name}: already at {current_total}/{target_per_class}. Skipping.")
        return records

    needed = target_per_class - current_total
    print(
        f"\n{target.class_name}: existing {current_total}/{target_per_class}. "
        f"Need {needed} new images."
    )

    for search_query in target.search_queries:
        if current_total >= target_per_class:
            break

        query_base_url = search_url_for(search_query)
        print(f"Query: {search_query}")
        downloaded_in_query = 0

        for page_number in range(1, max_pages_per_query + 1):
            if current_total >= target_per_class:
                break

            paged_url = with_page(query_base_url, page_number)
            print(f"  Opening page {page_number}: {paged_url}")
            driver.get(paged_url)
            time.sleep(delay_seconds + random.uniform(0.5, 1.5))
            scroll_results(driver, scroll_rounds, delay_seconds)

            candidates = parse_products(driver.page_source)
            print(f"  Found {len(candidates)} candidates on page {page_number}")

            new_downloads_on_page = 0
            for candidate in candidates:
                if current_total >= target_per_class:
                    break
                if candidate.image_url in known_image_urls:
                    continue

                try:
                    image_path = download_image(candidate.image_url, target.image_dir)
                except ImageDownloadError as exc:
                    print(f"  Skipped broken image for {target.class_name}: {exc}")
                    continue

                known_image_urls.add(candidate.image_url)
                record = ProductRecord(
                    image_url=candidate.image_url,
                    image_path=str(image_path.relative_to(PROJECT_ROOT)),
                    product_title=candidate.product_title,
                    brand=candidate.brand,
                    class_name=target.class_name,
                    gender=target.gender,
                    sleeve=target.sleeve,
                    product_url=candidate.product_url,
                )
                records.append(record)
                new_downloads_on_page += 1
                downloaded_in_query += 1
                current_total += 1
                print(
                    f"  Progress {target.class_name}: {current_total}/{target_per_class} "
                    f"(new this run: {len(records)})"
                )

            if new_downloads_on_page == 0 and page_number >= 2:
                print("  No new downloads on this page. Moving to next query.")
                break

    if current_total < target_per_class:
        print(
            f"{target.class_name}: completed with {current_total}/{target_per_class}. "
            f"Exhausted queries without enough new items."
        )
    else:
        print(f"{target.class_name}: target reached at {current_total}/{target_per_class}.")

    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape Myntra product images for FashTag.")
    parser.add_argument("--target-per-class", type=int, default=DEFAULT_TARGET_PER_CLASS)
    parser.add_argument("--scroll-rounds", type=int, default=DEFAULT_SCROLL_ROUNDS)
    parser.add_argument("--max-pages-per-query", type=int, default=DEFAULT_MAX_PAGES_PER_QUERY)
    parser.add_argument("--delay-seconds", type=float, default=DEFAULT_DELAY_SECONDS)
    parser.add_argument(
        "--headless",
        choices=("true", "false"),
        default="true",
        help="Run Chrome in headless mode.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_data_directories()
    known_urls = existing_image_urls(METADATA_CSV)
    class_counts = class_counts_by_name(METADATA_CSV)

    driver = build_driver(headless=args.headless == "true")
    try:
        for target in SCRAPE_TARGETS:
            existing_count = class_counts.get(target.class_name, 0)
            records = scrape_target(
                driver,
                target,
                target_per_class=args.target_per_class,
                already_in_metadata=existing_count,
                known_image_urls=known_urls,
                scroll_rounds=args.scroll_rounds,
                delay_seconds=args.delay_seconds,
                max_pages_per_query=args.max_pages_per_query,
            )
            append_records(METADATA_CSV, records)
            class_counts[target.class_name] = existing_count + len(records)
            print(f"Saved {len(records)} new records for {target.class_name}")
    except WebDriverException as exc:
        print(f"Selenium failed: {exc}")
        raise
    finally:
        driver.quit()

    print(f"\nMetadata saved to: {METADATA_CSV}")


if __name__ == "__main__":
    main()
