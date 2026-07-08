#!/usr/bin/env python3
"""
build_odoo_embed.py
--------------------
Run this from inside the manual's folder whenever you've updated the
manual and need a fresh single-file version to paste into Odoo's
"Embed Code" block.

What it does:
- Reads the main .html file
- Inlines the CSS file (assets/manual.css) into a <style> tag
- Inlines the captions JS (assets/captions.js) into a <script> tag
- Inlines the lightbox/caption <script> that's already in the HTML (kept as-is)
- Converts the logo and every screenshot image referenced via <img src="assets/...">
  into base64 data URIs, so there's no dependency on a separate assets folder
- Writes the result to build/odoo_embed.html

Usage:
    python3 build_odoo_embed.py

Then open build/odoo_embed.html, select all, copy, and paste into the
Odoo Embed Code block (replacing whatever was there before).

Requires no installs - uses only Python's standard library.
"""
import base64
import mimetypes
import re
import sys
from pathlib import Path

FOLDER = Path(__file__).parent
OUTPUT_DIR = FOLDER / "build"
OUTPUT_FILE = OUTPUT_DIR / "odoo_embed.html"


def find_main_html():
    html_files = [f for f in FOLDER.glob("*.html") if f.name != OUTPUT_FILE.name]
    if not html_files:
        sys.exit("No .html file found in this folder.")
    if len(html_files) > 1:
        print("Multiple .html files found, using the first one:", html_files[0].name)
    return html_files[0]


def inline_css(html, folder):
    def repl(match):
        href = match.group(1)
        css_path = folder / href
        if not css_path.exists():
            print(f"  ! CSS file not found, skipping: {href}")
            return match.group(0)
        css_text = css_path.read_text()
        print(f"  - inlined CSS: {href}")
        return f"<style>\n{css_text}\n</style>"

    return re.sub(
        r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)["\'][^>]*>',
        repl,
        html,
    )


def inline_external_scripts(html, folder):
    def repl(match):
        src = match.group(1)
        js_path = folder / src
        if not js_path.exists():
            print(f"  ! JS file not found, skipping: {src}")
            return match.group(0)
        js_text = js_path.read_text()
        print(f"  - inlined JS: {src}")
        return f"<script>\n{js_text}\n</script>"

    # Matches <script src="..." ...></script> (self-closing style with src attr)
    return re.sub(
        r'<script[^>]+src=["\']([^"\']+)["\'][^>]*>\s*</script>',
        repl,
        html,
    )


def inline_images(html, folder):
    def repl(match):
        prefix, src, suffix = match.group(1), match.group(2), match.group(3)
        img_path = folder / src
        if not img_path.exists():
            print(f"  ! Image not found, skipping: {src}")
            return match.group(0)
        mime, _ = mimetypes.guess_type(str(img_path))
        mime = mime or "application/octet-stream"
        data = base64.b64encode(img_path.read_bytes()).decode("ascii")
        print(f"  - inlined image: {src} ({len(data) // 1024} KB base64)")
        return f'{prefix}src="data:{mime};base64,{data}"{suffix}'

    return re.sub(
        r'(<img[^>]*?\s)src=["\']([^"\']+)["\']([^>]*>)',
        repl,
        html,
    )


def main():
    html_path = find_main_html()
    print(f"Reading: {html_path.name}")
    html = html_path.read_text()

    print("Inlining CSS...")
    html = inline_css(html, FOLDER)

    print("Inlining external JS files (e.g. captions.js)...")
    html = inline_external_scripts(html, FOLDER)

    print("Inlining images (logo + screenshots) as base64...")
    html = inline_images(html, FOLDER)

    OUTPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(html)

    size_kb = OUTPUT_FILE.stat().st_size // 1024
    print(f"\nDone. Wrote {OUTPUT_FILE.relative_to(FOLDER)} ({size_kb} KB).")
    print("Open that file, select all, copy, and paste into the Odoo Embed Code block.")


if __name__ == "__main__":
    main()
