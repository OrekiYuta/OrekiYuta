#!/usr/bin/env python3
"""Convert the Credly action's table cells to explicitly sized HTML images."""

from html import escape
import os
from pathlib import Path
import re


SECTION_START = "<!--START_SECTION:credly-badges-->"
SECTION_END = "<!--END_SECTION:credly-badges-->"
BADGE_PATTERN = re.compile(
    r"\[!\[(.*?)\]\((https?://[^\s]+?)\)\]\((https?://[^\s]+?)\)"
)
# Credly serves this PNG as application/octet-stream, which GitHub Camo rejects.
IMAGE_OVERRIDES = {
    "d739a868-f29a-4754-a49c-cde9ac936ef7": "assets/badges/instructlab-foundational.png",
}


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

    def render_badge(match):
        name, image, link = match.groups()
        for image_id, local_path in IMAGE_OVERRIDES.items():
            if f"/images/{image_id}/" in image:
                image = local_path
                break
        name, image, link = (escape(value, quote=True) for value in (name, image, link))
        return (
            f'<a href="{link}" title="{name}">'
            f'<img src="{image}" alt="{name}" width="{width}" height="{height}" />'
            "</a>"
        )

    section = BADGE_PATTERN.sub(render_badge, section)
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
        print("Badge images formatted with explicit dimensions.")
    else:
        print("Badge layout already up to date.")


if __name__ == "__main__":
    main()
