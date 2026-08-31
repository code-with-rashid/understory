#!/usr/bin/env python3
"""Generate correctly wired chapter skeletons, so authors write prose only.

    python3 scaffold.py init "How micrograd Works" --palette pine
    python3 scaffold.py chapter 3 forward-pass --title "The forward pass" \
            --parts beat,annotated,thread,check
    python3 scaffold.py parts

Every emitted file is already wired to course.js. Replace the TODO text and
nothing else; `verify.py` fails while any TODO remains.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNIPPETS = HERE / "snippets"

DEFAULT_PARTS = ["beat", "annotated", "beat", "check"]
COPY_INTO_COURSE = ["course.css", "course.js", "shell.html", "build.py", "verify.py",
                    "scaffold.py", "figures.py"]


def snippet(name: str) -> str:
    path = SNIPPETS / f"{name}.html"
    if not path.exists():
        sys.exit(f"scaffold: no part named {name!r}. Run `scaffold.py parts` to list them.")
    return path.read_text(encoding="utf-8").rstrip("\n")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


STARTERS = {
    "flow": {"type": "flow", "title": "", "desc": "", "caption": "",
             "zones": [{"label": "TODO zone", "nodes": ["a", "b"]}],
             "nodes": [{"id": "a", "label": "TODO", "note": "TODO"},
                       {"id": "b", "label": "TODO", "note": "TODO"}],
             "edges": [{"from": "a", "to": "b", "label": "TODO"}]},
    "sequence": {"type": "sequence", "title": "", "desc": "", "caption": "",
                 "lanes": [{"id": "a", "label": "TODO"}, {"id": "b", "label": "TODO"}],
                 "steps": [{"from": "a", "to": "b", "label": "TODO"},
                           {"at": "b", "note": "TODO what it does before replying"},
                           {"from": "b", "to": "a", "label": "TODO", "dashed": True}]},
    "layers": {"type": "layers", "title": "", "desc": "", "caption": "",
               "layers": [{"label": "TODO outer", "note": "TODO"},
                          {"label": "TODO middle", "note": "TODO"},
                          {"label": "TODO inner", "note": "TODO"}],
               "arrow": "inward", "arrowLabel": "depends on"},
    "states": {"type": "states", "title": "", "desc": "", "caption": "",
               "states": [{"id": "a", "label": "TODO"}, {"id": "b", "label": "TODO", "final": True}],
               "transitions": [{"from": "a", "to": "b", "label": "TODO"}]},
    "bars": {"type": "bars", "title": "", "desc": "", "caption": "", "unit": "TODO",
             "bars": [{"label": "TODO", "value": 10, "highlight": True},
                      {"label": "TODO", "value": 4}]},
}


def cmd_figure(args) -> int:
    root = Path(args.root).resolve()
    (root / "diagrams").mkdir(parents=True, exist_ok=True)
    dest = root / "diagrams" / f"{slug(args.name)}.json"
    if dest.exists() and not args.force:
        sys.exit(f"scaffold: {dest.name} already exists (use --force to overwrite)")
    dest.write_text(json.dumps(STARTERS[args.kind], indent=2) + "\n", encoding="utf-8")
    print(f"wrote {dest.relative_to(root)}")
    print(f'  reference it with: <div class="figure" data-figure="{slug(args.name)}"></div>')
    return 0


def cmd_parts(_args) -> int:
    names = sorted(p.stem for p in SNIPPETS.glob("*.html"))
    print("Available parts:\n  " + "\n  ".join(names))
    print("\nEvery chapter needs at least: one annotated block, one check, and one gloss.")
    return 0


def cmd_init(args) -> int:
    root = Path(args.root).resolve()
    (root / "chapters").mkdir(parents=True, exist_ok=True)
    (root / "diagrams").mkdir(parents=True, exist_ok=True)

    for name in COPY_INTO_COURSE:
        src = HERE / name
        if src.exists():
            shutil.copy2(src, root / name)
    shutil.copytree(SNIPPETS, root / "snippets", dirs_exist_ok=True)

    cfg = {
        "title": args.title,
        "subtitle": args.subtitle or "",
        "palette": args.palette,
        "lang": "en",
        "source": args.source or "",
    }
    (root / "course.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    print(f"course scaffolded in {root}")
    print("  next: python3 scaffold.py chapter 1 <slug> --title \"...\" --parts beat,annotated,check")
    return 0


def cmd_chapter(args) -> int:
    root = Path(args.root).resolve()
    chapters = root / "chapters"
    chapters.mkdir(parents=True, exist_ok=True)

    n = args.number
    name = slug(args.slug)
    title = args.title or args.slug.replace("-", " ").capitalize()
    short = args.short or title

    parts = [p.strip() for p in (args.parts.split(",") if args.parts else DEFAULT_PARTS) if p.strip()]
    body = "\n\n".join(snippet(p) for p in parts)

    text = (
        snippet("chapter")
        .replace("CH_ID", f"ch-{n}")
        .replace("CH_SHORT", short)
        .replace("CH_NUM", f"{n:02d}")
        .replace("CH_TITLE", title)
        .replace("CH_BODY", body)
    )

    dest = chapters / f"{n:02d}-{name}.html"
    if dest.exists() and not args.force:
        sys.exit(f"scaffold: {dest.name} already exists (use --force to overwrite)")
    dest.write_text(text + "\n", encoding="utf-8")

    print(f"wrote {dest.relative_to(root)} with parts: {', '.join(parts)}")
    print(f"  {text.count('TODO')} TODO markers to replace")
    return 0


def cmd_gloss(args) -> int:
    gid = "g-" + slug(args.term)
    out = (
        snippet("gloss")
        .replace("GLOSS_ID", gid)
        .replace("TODO term", args.term)
    )
    print(out)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="course directory (default: .)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def with_root(parser):
        # accepted before or after the subcommand, because both read naturally
        parser.add_argument("--root", default=argparse.SUPPRESS, help="course directory (default: .)")
        return parser

    p = with_root(sub.add_parser("init", help="create a new course directory"))
    p.add_argument("title")
    p.add_argument("--subtitle", default="")
    p.add_argument("--palette", default="pine",
                   choices=["pine", "clay", "indigo", "moss", "plum", "slate"])
    p.add_argument("--source", default="", help="path to the codebase being taught")
    p.set_defaults(func=cmd_init)

    p = with_root(sub.add_parser("chapter", help="create a wired chapter skeleton"))
    p.add_argument("number", type=int)
    p.add_argument("slug")
    p.add_argument("--title", default="")
    p.add_argument("--short", default="", help="rail label (defaults to the title)")
    p.add_argument("--parts", default="", help="comma-separated, in order. See `scaffold.py parts`")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_chapter)

    p = with_root(sub.add_parser("gloss", help="print a wired inline definition for a term"))
    p.add_argument("term")
    p.set_defaults(func=cmd_gloss)

    p = with_root(sub.add_parser("figure", help="create a starter diagram spec"))
    p.add_argument("kind", choices=sorted(STARTERS))
    p.add_argument("name")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_figure)

    p = sub.add_parser("parts", help="list available parts")
    p.set_defaults(func=cmd_parts)

    args = ap.parse_args()
    if not hasattr(args, "root"):
        args.root = "."
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
