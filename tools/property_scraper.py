#!/usr/bin/env python3
"""
Simple property listing scraper.

Fetches public listing pages and extracts readable body text plus images into
Markdown/JSON files that are easy to upload or paste into ChatGPT.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser
from pathlib import Path


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; PersonalPropertyNotes/1.0; "
    "+https://example.invalid/local-tool)"
)

SKIP_TAGS = {"script", "style", "noscript", "svg", "canvas", "iframe"}
TEXT_TAGS = {
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "li",
    "blockquote",
    "figcaption",
    "td",
    "th",
    "span",
    "div",
}
IMAGE_ATTRS = ("src", "data-src", "data-original", "data-lazy-src")
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".avif")
ROBOTS_CACHE: dict[str, urllib.robotparser.RobotFileParser] = {}


class ListingHTMLParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title_parts: list[str] = []
        self.text_chunks: list[str] = []
        self.headings: list[str] = []
        self.images: list[str] = []
        self.meta: dict[str, str] = {}
        self.json_ld: list[object] = []
        self._tag_stack: list[str] = []
        self._skip_depth = 0
        self._capture_title = False
        self._capture_json_ld = False
        self._json_ld_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr = {name.lower(): value or "" for name, value in attrs}
        self._tag_stack.append(tag)

        if tag in SKIP_TAGS:
            self._skip_depth += 1

        if tag == "title":
            self._capture_title = True

        if tag == "script" and "ld+json" in attr.get("type", "").lower():
            self._capture_json_ld = True
            self._json_ld_parts = []
            self._skip_depth = max(0, self._skip_depth - 1)

        if tag == "meta":
            key = attr.get("property") or attr.get("name")
            content = attr.get("content")
            if key and content:
                self.meta[key.lower()] = clean_space(content)
                if key.lower() in {"og:image", "twitter:image"}:
                    self._add_image(content)

        if tag in {"img", "source"}:
            for name in IMAGE_ATTRS:
                if attr.get(name):
                    self._add_image(attr[name])
            if attr.get("srcset"):
                for candidate in parse_srcset(attr["srcset"]):
                    self._add_image(candidate)

        if tag == "a" and attr.get("href"):
            href = attr["href"]
            if any(ext in href.lower() for ext in IMAGE_EXTS):
                self._add_image(href)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag == "title":
            self._capture_title = False

        if tag == "script" and self._capture_json_ld:
            self._capture_json_ld = False
            raw = "".join(self._json_ld_parts).strip()
            if raw:
                try:
                    self.json_ld.append(json.loads(raw))
                except json.JSONDecodeError:
                    pass

        if tag in SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1

        if self._tag_stack:
            self._tag_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._capture_json_ld:
            self._json_ld_parts.append(data)
            return

        if self._skip_depth:
            return

        text = clean_space(data)
        if not text:
            return

        if self._capture_title:
            self.title_parts.append(text)
            return

        tag = self._tag_stack[-1] if self._tag_stack else ""
        if tag in TEXT_TAGS:
            self.text_chunks.append(text)
            if tag in {"h1", "h2", "h3", "h4"}:
                self.headings.append(text)

    def _add_image(self, url: str) -> None:
        url = html.unescape(url.strip())
        if not url or url.startswith("data:"):
            return
        absolute = urllib.parse.urljoin(self.base_url, url)
        parsed = urllib.parse.urlparse(absolute)
        if parsed.scheme not in {"http", "https"}:
            return
        self.images.append(absolute)


def clean_space(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def parse_srcset(srcset: str) -> list[str]:
    candidates = []
    for part in srcset.split(","):
        url = part.strip().split(" ")[0]
        if url:
            candidates.append(url)
    return candidates


def unique_keep_order(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        marker = value.lower()
        if marker not in seen:
            seen.add(marker)
            result.append(value)
    return result


def meaningful_text(chunks: list[str]) -> list[str]:
    result = []
    previous = ""
    for chunk in chunks:
        if len(chunk) < 3:
            continue
        if chunk == previous:
            continue
        previous = chunk
        result.append(chunk)
    return result


def slug_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.strip("/").replace("/", "-")
    base = clean_filename(path or parsed.netloc or "listing")
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return f"{base[:70]}-{digest}"


def clean_filename(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "listing"


def fetch(url: str, timeout: int, user_agent: str) -> tuple[bytes, str]:
    if not allowed_by_robots(url, user_agent):
        raise PermissionError(f"blocked by robots.txt: {url}")

    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("content-type", "")
        return response.read(), content_type


def allowed_by_robots(url: str, user_agent: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    robots = ROBOTS_CACHE.get(origin)

    if robots is None:
        robots = urllib.robotparser.RobotFileParser()
        robots.set_url(urllib.parse.urljoin(origin, "/robots.txt"))
        try:
            robots.read()
        except (urllib.error.URLError, OSError):
            return True
        ROBOTS_CACHE[origin] = robots

    return robots.can_fetch(user_agent, url)


def decode_html(raw: bytes, content_type: str) -> str:
    match = re.search(r"charset=([\w.-]+)", content_type, re.I)
    encodings = [match.group(1)] if match else []
    encodings.extend(["utf-8", "latin-1"])

    for encoding in encodings:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def extract_listing(url: str, timeout: int, user_agent: str) -> dict[str, object]:
    raw, content_type = fetch(url, timeout, user_agent)
    parser = ListingHTMLParser(url)
    parser.feed(decode_html(raw, content_type))

    meta_description = (
        parser.meta.get("description")
        or parser.meta.get("og:description")
        or parser.meta.get("twitter:description")
        or ""
    )
    title = (
        clean_space(" ".join(parser.title_parts))
        or parser.meta.get("og:title")
        or parser.meta.get("twitter:title")
        or url
    )

    json_text = extract_json_ld_text(parser.json_ld)
    text = meaningful_text([meta_description, *parser.headings, *parser.text_chunks, *json_text])

    return {
        "url": url,
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "title": title,
        "description": meta_description,
        "headings": unique_keep_order(parser.headings),
        "text": unique_keep_order(text),
        "images": unique_keep_order(parser.images),
    }


def extract_json_ld_text(items: list[object]) -> list[str]:
    found: list[str] = []

    def walk(value: object, key: str = "") -> None:
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                walk(child_value, str(child_key).lower())
        elif isinstance(value, list):
            for child in value:
                walk(child, key)
        elif isinstance(value, str) and key in {
            "name",
            "headline",
            "description",
            "streetaddress",
            "addresslocality",
        }:
            cleaned = clean_space(value)
            if cleaned:
                found.append(cleaned)

    walk(items)
    return found


def markdown_for(data: dict[str, object], local_images: list[str]) -> str:
    lines = [
        f"# {data['title']}",
        "",
        f"Source: {data['url']}",
        f"Fetched: {data['fetched_at']}",
        "",
    ]

    description = str(data.get("description") or "")
    if description:
        lines.extend(["## Kort beskrivning", "", description, ""])

    lines.extend(["## Brödtext", ""])
    for paragraph in data.get("text", []):
        lines.extend([str(paragraph), ""])

    images = list(data.get("images", []))
    lines.extend(["## Bilder", ""])
    if not images:
        lines.extend(["Inga bilder hittades i sidans HTML.", ""])
    else:
        for index, image_url in enumerate(images, start=1):
            suffix = ""
            if index <= len(local_images):
                suffix = f"  \nLocal file: {local_images[index - 1]}"
            lines.extend([f"{index}. {image_url}{suffix}"])
        lines.append("")

    return "\n".join(lines)


def download_images(
    image_urls: list[str],
    image_dir: Path,
    max_images: int,
    timeout: int,
    user_agent: str,
    delay: float,
) -> list[str]:
    image_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []

    for index, image_url in enumerate(image_urls[:max_images], start=1):
        try:
            raw, content_type = fetch(image_url, timeout, user_agent)
        except (urllib.error.URLError, TimeoutError, OSError, PermissionError) as exc:
            print(f"Varning: kunde inte ladda ned bild {image_url}: {exc}", file=sys.stderr)
            continue

        extension = extension_for(image_url, content_type)
        filename = image_dir / f"image-{index:02d}{extension}"
        filename.write_bytes(raw)
        saved.append(str(filename))
        if delay:
            time.sleep(delay)

    return saved


def extension_for(url: str, content_type: str) -> str:
    content_type = content_type.lower()
    if "png" in content_type:
        return ".png"
    if "webp" in content_type:
        return ".webp"
    if "avif" in content_type:
        return ".avif"
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"

    path = urllib.parse.urlparse(url).path.lower()
    for extension in IMAGE_EXTS:
        if path.endswith(extension):
            return extension
    return ".jpg"


def save_listing(
    data: dict[str, object],
    out_dir: Path,
    download: bool,
    max_images: int,
    timeout: int,
    user_agent: str,
    delay: float,
) -> Path:
    slug = slug_from_url(str(data["url"]))
    listing_dir = out_dir / slug
    listing_dir.mkdir(parents=True, exist_ok=True)

    local_images: list[str] = []
    if download:
        local_images = download_images(
            list(data.get("images", [])),
            listing_dir / "images",
            max_images,
            timeout,
            user_agent,
            delay,
        )

    (listing_dir / "listing.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (listing_dir / "listing.md").write_text(
        markdown_for(data, local_images),
        encoding="utf-8",
    )
    return listing_dir / "listing.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape public property listing text and images into Markdown/JSON."
    )
    parser.add_argument("urls", nargs="+", help="One or more listing URLs.")
    parser.add_argument("--out", default="scrapes", help="Output directory.")
    parser.add_argument("--download-images", action="store_true", help="Download images locally.")
    parser.add_argument("--max-images", type=int, default=30, help="Max images to download per URL.")
    parser.add_argument("--timeout", type=int, default=20, help="Request timeout in seconds.")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between image downloads.")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT, help="HTTP User-Agent header.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    exit_code = 0
    for url in args.urls:
        try:
            data = extract_listing(url, args.timeout, args.user_agent)
            path = save_listing(
                data,
                out_dir,
                args.download_images,
                args.max_images,
                args.timeout,
                args.user_agent,
                args.delay,
            )
            print(f"Sparade: {path}")
        except (urllib.error.URLError, TimeoutError, OSError, PermissionError) as exc:
            print(f"Fel: kunde inte scrapea {url}: {exc}", file=sys.stderr)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
