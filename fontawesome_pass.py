#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fontawesome_pass.py
====================
Walks a Django templates folder (recursively - including subfolders like
"result/"), replaces every emoji with an equivalent Font Awesome icon, and
inserts the Font Awesome CDN link into every page's <head> if it's not
already there.

SAFE BY DESIGN:
- Makes a full backup of the entire templates folder before touching anything.
- Only ever replaces emoji/arrow *characters* - never touches Django template
  syntax ({% %}, {{ }}), HTML tags, or attribute structure.
- Emojis inside placeholder="..." text are removed (not turned into icons),
  since HTML can't render tags inside an attribute value.
- Running it twice is harmless - already-converted files are left alone.
- Prints a full report at the end: files changed, icons inserted, and any
  emoji it didn't recognize (so nothing is silently missed).

USAGE (single line, run from anywhere):
    python fontawesome_pass.py "C:\\path\\to\\accounts\\templates"

If you don't pass a path, it defaults to the current folder.
"""

import os
import re
import sys
import shutil
from datetime import datetime

# ------------------------------------------------------------------
# EMOJI -> FONT AWESOME MAPPING
# Same concept = same icon everywhere, for a consistent look app-wide.
# ------------------------------------------------------------------
EMOJI_MAP = {
    # Roles / people
    "🔑": "fa-solid fa-key",
    "👔": "fa-solid fa-user-tie",
    "🤵": "fa-solid fa-user-tie",
    "👨‍🏫": "fa-solid fa-chalkboard-user",
    "🧑‍🏫": "fa-solid fa-chalkboard-user",
    "👨‍🎓": "fa-solid fa-user-graduate",
    "🧑‍🎓": "fa-solid fa-user-graduate",
    "👑": "fa-solid fa-crown",
    "🧰": "fa-solid fa-toolbox",
    "👨‍👩‍👧‍👦": "fa-solid fa-people-roof",
    "👤": "fa-solid fa-user",
    "🧑": "fa-solid fa-user",
    "👨‍💼": "fa-solid fa-user-tie",

    # Money / finance
    "💰": "fa-solid fa-sack-dollar",
    "💳": "fa-solid fa-credit-card",
    "💵": "fa-solid fa-money-bill-wave",
    "💸": "fa-solid fa-money-bill-wave",

    # School / education
    "🏫": "fa-solid fa-school",
    "🎓": "fa-solid fa-graduation-cap",
    "📚": "fa-solid fa-book",
    "📖": "fa-solid fa-book-open",
    "📝": "fa-solid fa-pen",

    # Cards / IDs
    "🆔": "fa-solid fa-id-card",
    "🪪": "fa-solid fa-id-card-clip",
    "🎫": "fa-solid fa-ticket",

    # Charts / results / reports
    "📊": "fa-solid fa-chart-column",
    "📈": "fa-solid fa-chart-line",
    "📉": "fa-solid fa-chart-line",
    "📋": "fa-solid fa-clipboard-list",
    "📑": "fa-solid fa-file-lines",
    "🧾": "fa-solid fa-receipt",

    # Actions
    "⚙️": "fa-solid fa-gear",
    "🔐": "fa-solid fa-lock",
    "🔒": "fa-solid fa-lock",
    "🛡️": "fa-solid fa-shield-halved",
    "⚠️": "fa-solid fa-triangle-exclamation",
    "🗑️": "fa-solid fa-trash",
    "🔄": "fa-solid fa-rotate",
    "🔍": "fa-solid fa-magnifying-glass",
    "✏️": "fa-solid fa-pen-to-square",
    "✅": "fa-solid fa-circle-check",
    "✓": "fa-solid fa-check",
    "❌": "fa-solid fa-xmark",
    "✕": "fa-solid fa-xmark",
    "✗": "fa-solid fa-xmark",
    "💬": "fa-solid fa-comment",
    "📤": "fa-solid fa-paper-plane",
    "👁️": "fa-solid fa-eye",
    "👀": "fa-solid fa-eye",
    "🖨️": "fa-solid fa-print",
    "➕": "fa-solid fa-plus",
    "💾": "fa-solid fa-floppy-disk",
    "📌": "fa-solid fa-thumbtack",
    "📷": "fa-solid fa-camera",
    "🔖": "fa-solid fa-bookmark",

    # Time / dates
    "📆": "fa-solid fa-calendar-days",
    "📅": "fa-solid fa-calendar-days",
    "🕐": "fa-solid fa-clock",
    "⏰": "fa-solid fa-clock",
    "⏱️": "fa-solid fa-stopwatch",

    # Feedback / mood (used on result pages)
    "🎉": "fa-solid fa-champagne-glasses",
    "😊": "fa-solid fa-face-smile",
    "👍": "fa-solid fa-thumbs-up",
    "⭐": "fa-solid fa-star",
    "🔥": "fa-solid fa-fire",
    "🏆": "fa-solid fa-trophy",
    "🥇": "fa-solid fa-medal",
    "🎁": "fa-solid fa-gift",
    "🚀": "fa-solid fa-rocket",
    "🎨": "fa-solid fa-palette",
    "💯": "fa-solid fa-percent",

    # Info / misc
    "ℹ️": "fa-solid fa-circle-info",
    "❗": "fa-solid fa-exclamation",
    "❓": "fa-solid fa-question",
    "👆": "fa-solid fa-hand-point-up",
    "🎯": "fa-solid fa-bullseye",
    "📞": "fa-solid fa-phone",

    # Found during testing against the full real template set
    "📥": "fa-solid fa-inbox",
    "📘": "fa-solid fa-book",
    "📇": "fa-solid fa-address-card",
    "🎭": "fa-solid fa-user-tag",
    "💡": "fa-solid fa-lightbulb",
    "🕒": "fa-solid fa-clock",
    "💙": "fa-solid fa-circle-info",

    # Arrows (plain glyphs, same treatment as emoji)
    "➡️": "fa-solid fa-arrow-right",
    "⬅️": "fa-solid fa-arrow-left",
    "→": "fa-solid fa-arrow-right",
    "←": "fa-solid fa-arrow-left",
}

FA_CDN_LINK = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">'

# Matches any leftover emoji-range character not in our map (for reporting only)
EMOJI_SCAN_PATTERN = re.compile(
    "[\U0001F300-\U0001FAFF\u2600-\u27BF\u2190-\u21FF\u2B00-\u2BFF\uFE0F]"
)

PLACEHOLDER_PATTERN = re.compile(r'placeholder=(["\'])(.*?)\1', re.DOTALL)


def strip_emoji_from_placeholders(content):
    """Placeholders can't contain HTML, so emojis there are just removed,
    not converted to icons. Runs BEFORE the main icon conversion."""
    def _clean(match):
        quote = match.group(1)
        text = match.group(2)
        for emoji in EMOJI_MAP:
            text = text.replace(emoji, "")
        text = EMOJI_SCAN_PATTERN.sub("", text)
        text = re.sub(r"\s{2,}", " ", text).strip()
        return f'placeholder={quote}{text}{quote}'
    return PLACEHOLDER_PATTERN.sub(_clean, content)


def convert_emojis_to_icons(content):
    """Replace every mapped emoji with an <i> Font Awesome tag."""
    count = 0
    # Sort by length descending so multi-character ZWJ sequences (e.g. family/teacher
    # emojis) are matched whole, before any shorter emoji they might contain.
    for emoji in sorted(EMOJI_MAP, key=len, reverse=True):
        fa_class = EMOJI_MAP[emoji]
        occurrences = content.count(emoji)
        if occurrences:
            content = content.replace(emoji, f'<i class="{fa_class}"></i>')
            count += occurrences
    return content, count


def ensure_fa_cdn(content):
    """Insert the Font Awesome CDN link into <head> if it isn't already there."""
    if "font-awesome" in content:
        return content, False

    if "</title>" in content:
        content = content.replace("</title>", f"</title>\n    {FA_CDN_LINK}", 1)
        return content, True

    if "<head>" in content:
        content = content.replace("<head>", f"<head>\n    {FA_CDN_LINK}", 1)
        return content, True

    # No <head> at all (unusual) - leave it, nothing safe to anchor to
    return content, False


def process_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    content = strip_emoji_from_placeholders(content)
    content, icon_count = convert_emojis_to_icons(content)
    content, cdn_added = ensure_fa_cdn(content)

    leftover = set(EMOJI_SCAN_PATTERN.findall(content))

    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    return icon_count, cdn_added, leftover


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    root = os.path.abspath(root)

    if not os.path.isdir(root):
        print(f"ERROR: '{root}' is not a folder.")
        sys.exit(1)

    # ---- Backup first, always ----
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"{root}_backup_{timestamp}"
    shutil.copytree(root, backup_dir)
    print(f"Backup created at: {backup_dir}\n")

    html_files = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(".html"):
                html_files.append(os.path.join(dirpath, fn))

    if not html_files:
        print("No .html files found. Nothing to do.")
        return

    total_icons = 0
    total_cdn_added = 0
    files_changed = 0
    all_leftovers = {}

    for path in sorted(html_files):
        rel = os.path.relpath(path, root)
        icon_count, cdn_added, leftover = process_file(path)

        if icon_count or cdn_added:
            files_changed += 1
        total_icons += icon_count
        total_cdn_added += 1 if cdn_added else 0

        if leftover:
            all_leftovers[rel] = leftover

        status = []
        if icon_count:
            status.append(f"{icon_count} icon(s) converted")
        if cdn_added:
            status.append("FA CDN link added")
        if leftover:
            status.append(f"UNRECOGNIZED: {' '.join(leftover)}")
        print(f"  {rel:55s} {' | '.join(status) if status else '(no change)'}")

    print("\n" + "=" * 60)
    print(f"Done. {len(html_files)} file(s) scanned, {files_changed} changed.")
    print(f"Total icons converted: {total_icons}")
    print(f"Font Awesome CDN link added to: {total_cdn_added} file(s)")
    if all_leftovers:
        print("\nFiles with emoji this script didn't recognize (left as-is):")
        for rel, chars in all_leftovers.items():
            print(f"  - {rel}: {' '.join(chars)}")
        print("\nSend me these characters and I'll add them to the mapping.")
    print(f"\nYour original files are safely backed up at:\n  {backup_dir}")


if __name__ == "__main__":
    main()