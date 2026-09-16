#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
responsive_pass.py
====================
Walks a Django templates folder (recursively) and upgrades mobile
responsiveness WITHOUT touching any logic, Django tags, or existing design -
only adds what's missing:

1. Adds the viewport meta tag if a page is missing it.
2. Wraps any un-wrapped <table> in a horizontally-scrollable container, so
   wide tables don't break the page layout on a phone (only for tables that
   aren't already handled some other way).
3. Finds rigid multi-column CSS grids (e.g. `repeat(3, 1fr)`) that have no
   mobile override, and adds a media query that stacks them to a single
   column under 720px.
4. Adds a mobile stacking rule for `.navbar` if it uses flex and has none.

SAFE BY DESIGN:
- Makes a full backup of the folder before changing anything.
- Only ADDS css/markup - never removes or rewrites existing rules.
- Skips any file/selector that already has responsive handling, so running
  it on an already-good file is a no-op.
- Running it twice is harmless.
- Prints a full per-file report of exactly what was added.

USAGE (single line):
    python responsive_pass.py "accounts\\templates"
"""

import os
import re
import sys
import shutil
from datetime import datetime

VIEWPORT_TAG = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
TABLE_WRAP_CLASS = "table-scroll-wrap"
TABLE_WRAP_CSS = (
    f".{TABLE_WRAP_CLASS} {{ width: 100%; overflow-x: auto; "
    "-webkit-overflow-scrolling: touch; }"
)
GRID_BREAKPOINT = 720
NAVBAR_BREAKPOINT = 768

TABLE_BLOCK_RE = re.compile(r"(<table\b[^>]*>.*?</table>)", re.DOTALL | re.IGNORECASE)
ALREADY_WRAPPED_RE = re.compile(
    r'<div[^>]*class="[^"]*\btable-scroll-wrap\b', re.IGNORECASE
)
TABLE_HANDLED_RE = re.compile(r"overflow-x\s*:\s*auto", re.IGNORECASE)

STYLE_BLOCK_RE = re.compile(r"(<style[^>]*>)(.*?)(</style>)", re.DOTALL | re.IGNORECASE)

# selector { ... grid-template-columns: repeat(N, 1fr) ... }
GRID_RULE_RE = re.compile(
    r"([^\{\}]+?)\{([^{}]*?grid-template-columns\s*:\s*repeat\(\s*([2-9])\s*,\s*1fr\s*\)[^{}]*)\}",
    re.DOTALL,
)

NAVBAR_FLEX_RE = re.compile(r"\.navbar\s*\{[^{}]*display\s*:\s*flex[^{}]*\}", re.DOTALL)


def ensure_viewport(content):
    if 'name="viewport"' in content:
        return content, False
    if "<head>" not in content:
        return content, False
    if 'charset="UTF-8"' in content or "charset='UTF-8'" in content:
        content = re.sub(
            r'(<meta charset=["\']UTF-8["\']\s*/?>)',
            r"\1\n    " + VIEWPORT_TAG,
            content,
            count=1,
            flags=re.IGNORECASE,
        )
        return content, True
    content = content.replace("<head>", f"<head>\n    {VIEWPORT_TAG}", 1)
    return content, True


def wrap_tables(content):
    """Wrap every <table>...</table> in a scroll container, unless the file
    already handles table overflow some other way (e.g. table itself set to
    display:block + overflow-x, as several dashboards already do)."""
    if TABLE_HANDLED_RE.search(content) or ALREADY_WRAPPED_RE.search(content):
        return content, 0

    count = 0

    def _wrap(match):
        nonlocal count
        count += 1
        return f'<div class="{TABLE_WRAP_CLASS}">\n{match.group(1)}\n</div>'

    new_content = TABLE_BLOCK_RE.sub(_wrap, content)
    return new_content, count


def add_table_css(content, tables_wrapped):
    if tables_wrapped == 0:
        return content, False
    if TABLE_WRAP_CLASS in content.split("</style>")[0] if "</style>" in content else False:
        pass  # fallthrough - simpler check below
    # Avoid duplicating the CSS rule if it's already present
    if f".{TABLE_WRAP_CLASS}" in content:
        # already defined somewhere (e.g. re-run) - don't add again
        return content, False

    def _inject(m):
        return m.group(1) + m.group(2) + f"\n{TABLE_WRAP_CSS}\n" + m.group(3)

    if STYLE_BLOCK_RE.search(content):
        content = STYLE_BLOCK_RE.sub(_inject, content, count=1)
        return content, True
    return content, False


def collapse_rigid_grids(content):
    """Find rigid N-column grids with no existing mobile override and add one."""
    style_match = STYLE_BLOCK_RE.search(content)
    if not style_match:
        return content, []

    style_body = style_match.group(2)
    added_selectors = []
    new_rules = []

    for sel_match in GRID_RULE_RE.finditer(style_body):
        raw_selector = sel_match.group(1).strip()
        # Only handle simple, safe selectors (single class/id, no combinators)
        if not re.fullmatch(r"[.\#][\w-]+", raw_selector):
            continue

        # Skip if a media query already targets this exact selector
        already_handled = re.search(
            r"@media[^{]*\{[^@]*?" + re.escape(raw_selector) + r"\s*\{[^}]*grid-template-columns",
            style_body,
            re.DOTALL,
        )
        if already_handled:
            continue

        rule = f"{raw_selector} {{ grid-template-columns: 1fr; }}"
        if rule not in new_rules:
            new_rules.append(rule)
            added_selectors.append(raw_selector)

    if not new_rules:
        return content, []

    media_block = (
        f"\n@media (max-width: {GRID_BREAKPOINT}px) {{\n    "
        + "\n    ".join(new_rules)
        + "\n}\n"
    )

    def _inject(m):
        return m.group(1) + m.group(2) + media_block + m.group(3)

    content = STYLE_BLOCK_RE.sub(_inject, content, count=1)
    return content, added_selectors


def add_navbar_stack(content):
    style_match = STYLE_BLOCK_RE.search(content)
    if not style_match:
        return content, False

    style_body = style_match.group(2)

    if not NAVBAR_FLEX_RE.search(style_body):
        return content, False  # no flex navbar to worry about

    already_handled = re.search(
        r"@media[^{]*\{[^@]*?\.navbar\s*\{[^}]*flex-direction",
        style_body,
        re.DOTALL,
    )
    if already_handled:
        return content, False

    media_block = (
        f"\n@media (max-width: {NAVBAR_BREAKPOINT}px) {{\n"
        "    .navbar { flex-direction: column; gap: 10px; text-align: center; }\n"
        "}\n"
    )

    def _inject(m):
        return m.group(1) + m.group(2) + media_block + m.group(3)

    content = STYLE_BLOCK_RE.sub(_inject, content, count=1)
    return content, True


def process_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    original = content

    content, viewport_added = ensure_viewport(content)
    content, tables_wrapped = wrap_tables(content)
    content, table_css_added = add_table_css(content, tables_wrapped)
    content, grids_fixed = collapse_rigid_grids(content)
    content, navbar_fixed = add_navbar_stack(content)

    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    return {
        "viewport_added": viewport_added,
        "tables_wrapped": tables_wrapped,
        "grids_fixed": grids_fixed,
        "navbar_fixed": navbar_fixed,
    }


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    root = os.path.abspath(root)

    if not os.path.isdir(root):
        print(f"ERROR: '{root}' is not a folder.")
        sys.exit(1)

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

    files_changed = 0
    totals = {"viewport": 0, "tables": 0, "grids": 0, "navbars": 0}

    for path in sorted(html_files):
        rel = os.path.relpath(path, root)
        result = process_file(path)

        status = []
        if result["viewport_added"]:
            status.append("viewport tag added")
            totals["viewport"] += 1
        if result["tables_wrapped"]:
            status.append(f"{result['tables_wrapped']} table(s) made scrollable")
            totals["tables"] += result["tables_wrapped"]
        if result["grids_fixed"]:
            status.append(f"grid(s) stacked on mobile: {', '.join(result['grids_fixed'])}")
            totals["grids"] += len(result["grids_fixed"])
        if result["navbar_fixed"]:
            status.append("navbar mobile-stacking added")
            totals["navbars"] += 1

        if status:
            files_changed += 1
        print(f"  {rel:55s} {' | '.join(status) if status else '(already fine - no change)'}")

    print("\n" + "=" * 60)
    print(f"Done. {len(html_files)} file(s) scanned, {files_changed} upgraded.")
    print(f"Viewport tags added: {totals['viewport']}")
    print(f"Tables made scrollable: {totals['tables']}")
    print(f"Grids given mobile stacking: {totals['grids']}")
    print(f"Navbars given mobile stacking: {totals['navbars']}")
    print(f"\nYour original files are safely backed up at:\n  {backup_dir}")


if __name__ == "__main__":
    main()