#!/usr/bin/env python3
"""Assemble a course from course.json + chapters/*.html into index.html.

    python3 build.py                       # build ./index.html
    python3 build.py --out dist/index.html
    python3 build.py --inline --out course-standalone.html

`--inline` folds the stylesheet and the engine into the page, producing one
file that can be emailed, dropped in a message, or opened from a USB stick
with nothing beside it.

The chapter rail is generated from the chapter files themselves, so the
navigation can never disagree with the chapters that actually exist.
"""
from __future__ import annotations

import argparse
import datetime
import html
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figures  # noqa: E402  (sits beside this file, copied into every course)

# Dark-mode accents are lightened until they clear WCAG AA (4.5:1) against the
# dark background; the light-mode values already clear it against the light one.
PALETTES = {
    # name:      accent     strong     wash       quiet      wash-dark  accent-dark quiet-dark
    "pine":   ("#0F6F76", "#0A565C", "#E4F1F1", "#7FB3B6", "#10262A", "#238D95", "#41A3AA"),
    "clay":   ("#B04A2F", "#8E3A23", "#FAEDE8", "#DA9A85", "#2B1712", "#CC5E41", "#CB8775"),
    "indigo": ("#3B4C9E", "#2C3A7D", "#EAECF8", "#9AA5D6", "#161A33", "#6979C7", "#8E9AD4"),
    "moss":   ("#3F6B33", "#325527", "#EBF2E6", "#9DBB90", "#16210F", "#538E43", "#69AE56"),
    "plum":   ("#8A3B62", "#6D2C4C", "#F8EAF1", "#C892AC", "#2A121F", "#BB608D", "#CA84A7"),
    "slate":  ("#41566B", "#324255", "#ECEFF3", "#9BAAB9", "#171D24", "#6381A0", "#829BB3"),
}

TITLE_RE = re.compile(r'<h1[^>]*class="chapter__title"[^>]*>(.*?)</h1>', re.S)
ID_RE = re.compile(r'<section[^>]*\bid="([^"]+)"', re.S)
SHORT_RE = re.compile(r'data-u-short="([^"]*)"')
TAG_RE = re.compile(r"<[^>]+>")


def die(msg: str) -> None:
    print(f"build: {msg}", file=sys.stderr)
    sys.exit(1)


def chapter_meta(path: Path, index: int) -> dict:
    text = path.read_text(encoding="utf-8")

    m = ID_RE.search(text)
    if not m:
        die(f"{path.name}: no <section id=\"...\"> found — every chapter needs one")
    cid = m.group(1)

    t = TITLE_RE.search(text)
    if not t:
        die(f'{path.name}: no <h1 class="chapter__title"> found')
    title = html.unescape(TAG_RE.sub("", t.group(1))).strip()

    s = SHORT_RE.search(text)
    short = s.group(1).strip() if s else title

    return {"id": cid, "title": title, "short": short, "n": index, "html": text}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="course directory (default: .)")
    ap.add_argument("--out", default=None, help="output file (default: <root>/index.html)")
    ap.add_argument("--inline", action="store_true",
                    help="fold course.css and course.js into the page — one shareable file")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    cfg_path = root / "course.json"
    if not cfg_path.exists():
        die("course.json not found — see guides/authoring.md for the fields it needs")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    title = cfg.get("title")
    if not title:
        die('course.json needs a "title"')

    palette = cfg.get("palette", "pine")
    if palette not in PALETTES:
        die(f"unknown palette {palette!r} — choose from: {', '.join(sorted(PALETTES))}")
    accent, strong, wash, quiet, wash_dark, accent_dark, quiet_dark = PALETTES[palette]

    shell_path = root / "shell.html"
    if not shell_path.exists():
        die("shell.html not found in the course directory")
    shell = shell_path.read_text(encoding="utf-8")

    chapter_dir = root / "chapters"
    files = sorted(p for p in chapter_dir.glob("*.html")) if chapter_dir.is_dir() else []
    if not files:
        die("no chapters/*.html found")

    chapters = [chapter_meta(p, i + 1) for i, p in enumerate(files)]

    seen: dict[str, str] = {}
    for c in chapters:
        if c["id"] in seen:
            die(f'two chapters share id="{c["id"]}" ({seen[c["id"]]} and this one)')
        seen[c["id"]] = c["id"]

    rail = "\n".join(
        '    <li><button class="u-rail__link" type="button" data-u-goto="{id}" aria-current="false">'
        '<span class="u-rail__num">{n:02d}</span>'
        '<span class="u-rail__label">{short}</span></button></li>'.format(
            id=c["id"], n=c["n"], short=html.escape(c["short"])
        )
        for c in chapters
    )

    body = "\n\n".join(c["html"].rstrip() for c in chapters)

    # Diagrams become inline SVG here rather than in the browser, so a course
    # keeps its pictures offline, in print, and with scripting switched off.
    drawn = 0

    def draw(match):
        nonlocal drawn
        name = match.group(1)
        try:
            svg = figures.render(figures.load(root, name), name)
        except (FileNotFoundError, ValueError, KeyError, json.JSONDecodeError) as err:
            die(f"figure {name!r}: {err}")
        drawn += 1
        return svg

    body = re.sub(r'<div class="figure"[^>]*data-figure="([\w-]+)"[^>]*>\s*</div>', draw, body)
    leftover = re.findall(r'data-figure="([\w-]+)"', body)
    if leftover:
        die(f"figure placeholder(s) not replaced: {', '.join(sorted(set(leftover)))} — "
            f'the tag must be exactly <div class="figure" data-figure="name"></div>')

    out = (
        shell.replace("{{LANG}}", cfg.get("lang", "en"))
        .replace("{{TITLE}}", html.escape(title))
        .replace("{{SUBTITLE}}", html.escape(cfg.get("subtitle", "")))
        .replace("{{ACCENT_STRONG}}", strong)
        .replace("{{ACCENT_WASH_DARK}}", wash_dark)
        .replace("{{ACCENT_DARK}}", accent_dark)
        .replace("{{ACCENT_QUIET_DARK}}", quiet_dark)
        .replace("{{ACCENT_WASH}}", wash)
        .replace("{{ACCENT_QUIET}}", quiet)
        .replace("{{ACCENT}}", accent)
        .replace("{{RAIL}}", rail)
        .replace("{{CHAPTERS}}", body)
    )

    if args.inline:
        css = (root / "course.css").read_text(encoding="utf-8")
        js = (root / "course.js").read_text(encoding="utf-8")
        # a literal </script> inside the source would close the tag early
        js = js.replace("</script", "<\\/script")
        out = out.replace(
            '<link rel="stylesheet" href="course.css">',
            "<style>\n" + css + "\n</style>",
        ).replace(
            '<script src="course.js" defer></script>',
            "<script>\n" + js + "\n</script>",
        )
        if "course.css" in out or 'src="course.js"' in out:
            die("inlining did not take — shell.html no longer matches the expected asset tags")

    # The page names the code it describes, so staleness is visible instead
    # of silent — the doc equivalent of a use-by date.
    source = cfg.get("source", "")
    src_path = (root / source).resolve() if source and not Path(source).is_absolute() else Path(source)
    colophon = f"Generated {datetime.date.today():%d %b %Y}"
    if source:
        stamp = f"Describes <code>{html.escape(Path(source).name)}</code>"
        try:
            sha = subprocess.run(["git", "-C", str(src_path), "rev-parse", "--short", "HEAD"],
                                 capture_output=True, text=True, timeout=10).stdout.strip()
            if sha:
                stamp += f" at commit <code>{html.escape(sha)}</code>"
        except (OSError, subprocess.SubprocessError):
            pass
        colophon = f"{stamp} · {colophon} · regenerate when the code moves on"
    out = out.replace("{{COLOPHON}}", colophon)

    leftovers = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if leftovers:
        die(f"unfilled placeholders remain: {', '.join(sorted(set(leftovers)))}")

    dest = Path(args.out) if args.out else root / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")

    size = dest.stat().st_size
    print(f"built {dest.relative_to(Path.cwd()) if dest.is_relative_to(Path.cwd()) else dest} "
          f"— {len(chapters)} chapters, {drawn} figures, palette {palette}, {size // 1024} KB"
          + (", self-contained" if args.inline else ""))
    return 0


if __name__ == "__main__":
    # Windows consoles default to a legacy code page that cannot encode the
    # check marks and dashes in our output; never let printing crash a run.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    raise SystemExit(main())
