#!/usr/bin/env python3
"""Convert the Credly action's table cells to explicitly sized HTML images."""

from html import escape, unescape
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import re
import time
import unicodedata
from urllib.parse import urlparse
from urllib.error import URLError
from urllib.request import Request, urlopen


SECTION_START = "<!--START_SECTION:credly-badges-->"
SECTION_END = "<!--END_SECTION:credly-badges-->"
BADGE_PATTERN = re.compile(
    r"\[!\[(.*?)\]\((https?://[^\s]+?)\)\]\((https?://[^\s]+?)\)"
)
HTML_BADGE_PATTERN = re.compile(
    r'(<a\b[^>]*\btitle="([^"]*)"[^>]*>\s*<img\b[^>]*\bsrc=")([^"]+)(")',
    re.IGNORECASE,
)


def badge_slug(name):
    name = unescape(name)
    slug = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug[:100].rstrip("-") or "badge-image"


def image_extension(data, content_type, image_url):
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ".webp"

    extension = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }.get(content_type.lower())
    if extension:
        return extension

    url_extension = Path(urlparse(image_url).path).suffix.lower()
    if url_extension in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        return ".jpg" if url_extension == ".jpeg" else url_extension
    raise ValueError(f"Could not determine image format for {image_url}")


def localize_image(image_url, badge_name):
    asset_dir = Path("assets/badges")
    asset_dir.mkdir(parents=True, exist_ok=True)
    local_stem = badge_slug(badge_name)

    if not image_url.startswith(("http://", "https://")):
        source_path = Path(image_url)
        if not source_path.is_file():
            raise FileNotFoundError(f"Badge image does not exist: {image_url}")
        local_path = asset_dir / f"{local_stem}{source_path.suffix.lower()}"
        if source_path.resolve() == local_path.resolve():
            return local_path.as_posix()
        if local_path.exists():
            local_path.write_bytes(source_path.read_bytes())
            if source_path.resolve().is_relative_to(asset_dir.resolve()):
                source_path.unlink()
        elif source_path.resolve().is_relative_to(asset_dir.resolve()):
            source_path.replace(local_path)
        else:
            local_path.write_bytes(source_path.read_bytes())
        return local_path.as_posix()

    existing_images = sorted(
        path for path in asset_dir.glob(f"{local_stem}.*") if path.stem == local_stem
    )
    if existing_images:
        return existing_images[0].as_posix()

    request = Request(image_url, headers={"User-Agent": "OrekiYuta-badge-downloader/1.0"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                data = response.read()
                content_type = response.headers.get_content_type()
            break
        except (URLError, TimeoutError, OSError) as error:
            if attempt == 2:
                raise RuntimeError(f"Failed to download badge image {image_url}: {error}") from error
            time.sleep(attempt + 1)

    extension = image_extension(data, content_type, image_url)
    local_path = asset_dir / f"{local_stem}{extension}"
    if not local_path.exists() or local_path.read_bytes() != data:
        local_path.write_bytes(data)
    return local_path.as_posix()


def format_badges(content, badge_size):
    size = re.fullmatch(r"([1-9]\d*)x([1-9]\d*)", badge_size)
    if not size:
        raise ValueError("BADGE_SIZE must be WIDTHxHEIGHT, e.g. 80x80")
    width, height = size.groups()

    before, start, remaining = content.partition(SECTION_START)
    section, end, after = remaining.partition(SECTION_END)
    if not start or not end:
        raise ValueError("Credly badge section markers are missing")
    if "<table>" not in section or "</table>" not in section:
        raise ValueError("Expected a badge table; set the action's columns input above 0")

    image_entries = {
        (match.group(3), unescape(match.group(2)))
        for match in HTML_BADGE_PATTERN.finditer(section)
    }
    image_entries.update(
        (match.group(2), unescape(match.group(1)))
        for match in BADGE_PATTERN.finditer(section)
    )
    with ThreadPoolExecutor(max_workers=8) as executor:
        local_images = dict(
            zip(image_entries, executor.map(lambda entry: localize_image(*entry), image_entries))
        )

    def render_badge(match):
        name, image, link = match.groups()
        image = local_images.get((image, unescape(name)), image)
        name, image, link = (escape(value, quote=True) for value in (name, image, link))
        return (
            f'<a href="{link}" title="{name}">'
            f'<img src="{image}" alt="{name}" width="{width}" height="{height}" />'
            "</a>"
        )

    section = BADGE_PATTERN.sub(render_badge, section)
    section = HTML_BADGE_PATTERN.sub(
        lambda match: match.group(1)
        + escape(local_images.get((match.group(3), unescape(match.group(2))), match.group(3)), quote=True)
        + match.group(4),
        section,
    )
    section = section.replace("<td>", '<td align="center" valign="middle">')
    section = section.replace("<tr><td", "<tr>\n    <td")
    section = section.replace("</td><td", "</td>\n    <td")
    section = section.replace("</td></tr>", "</td>\n  </tr>")
    return before + start + section + end + after


def main():
    readme = Path("README.md")
    content = readme.read_text(encoding="utf-8")
    formatted = format_badges(content, os.environ.get("BADGE_SIZE", "80x80"))
    if formatted != content:
        readme.write_text(formatted, encoding="utf-8")
        print("Badge images formatted and stored locally.")
    else:
        print("Badge layout and local images already up to date.")


if __name__ == "__main__":
    main()
