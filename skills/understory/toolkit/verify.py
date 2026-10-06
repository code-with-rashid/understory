#!/usr/bin/env python3
"""Check a built course for the failures that a browser does not report.

    python3 verify.py                     # check ./index.html
    python3 verify.py --src ../my-repo    # also check code snippets are verbatim
    python3 verify.py --strict            # treat warnings as failures

Exit status is non-zero if any ERROR is found (or any WARN under --strict).
"""
from __future__ import annotations

import argparse
import html as html_mod
import json
import re
import sys
from collections import Counter
from pathlib import Path

KNOWN_PARTS = {"rail", "progress", "check", "trace", "thread", "match", "hunt", "map", "stack", "gloss"}
TAG_RE = re.compile(r"<[^>]+>")
SENTENCE_RE = re.compile(r"[.!?](?:\s|$)")

VISUAL_MARKERS = ("annotated", "check", "trace", "thread", "match", "hunt",
                  "map", "stack", "cards", "steps", "rows", "tree", "aside",
                  "depth", "defend", "tradeoff", "figure",
                  "territory", "fieldwork", "recall", "myth")
INTERACTIVE_MARKERS = ('data-u="check"', 'data-u="trace"', 'data-u="thread"',
                       'data-u="match"', 'data-u="hunt"', 'data-u="map"', 'data-u="stack"')
TIRED_METAPHORS = ("restaurant", "kitchen", "recipe", "chef", "waiter")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warns: list[str] = []
        self.notes: list[str] = []

    def error(self, msg: str) -> None: self.errors.append(msg)
    def warn(self, msg: str) -> None: self.warns.append(msg)
    def note(self, msg: str) -> None: self.notes.append(msg)


def count_blocks(doc: str, name: str) -> int:
    """Count elements whose class list contains `name` as a whole token. A
    plain substring count also matches the block's own children — tradeoff__head
    reads as a tradeoff — which silently inflates every total."""
    return len(re.findall(r'class="(?:[^"]*\s)?' + re.escape(name) + r'(?:\s[^"]*)?"', doc))


def has_block(doc: str, name: str) -> bool:
    return count_blocks(doc, name) > 0


def markup_only(doc: str) -> str:
    """Drop <script> and <style> bodies. An inlined build carries the engine's
    own source, and selector strings inside it are not markup."""
    doc = re.sub(r"<script\b[^>]*>.*?</script>", "<script></script>", doc, flags=re.S | re.I)
    return re.sub(r"<style\b[^>]*>.*?</style>", "<style></style>", doc, flags=re.S | re.I)


def text_of(fragment: str) -> str:
    return html_mod.unescape(TAG_RE.sub("", fragment)).strip()


def attrs_of(tag: str) -> dict[str, str]:
    return {m.group(1): html_mod.unescape(m.group(2))
            for m in re.finditer(r'([a-zA-Z_][-\w]*)="([^"]*)"', tag)}


def spans_of_class(fragment: str, cls: str) -> list[str]:
    """Contents of every <span class="cls">, honouring nested spans — syntax
    colouring puts spans inside the line spans, so a lazy regex stops early."""
    out = []
    opener = re.compile(r'<span class="' + re.escape(cls) + r'"\s*>')
    for m in opener.finditer(fragment):
        depth, i = 1, m.end()
        for t in re.finditer(r"<(/?)span\b[^>]*>", fragment[m.end():]):
            depth += 1 if not t.group(1) else -1
            if depth == 0:
                i = m.end() + t.start()
                break
        out.append(fragment[m.end():i])
    return out


def without_gloss(fragment: str) -> str:
    """Definitions live inside the paragraph that references them but render in
    a popover, so they are not prose and must not be counted as prose."""
    out, i = [], 0
    for m in re.finditer(r'<span class="gloss-def"[^>]*>', fragment):
        if m.start() < i:
            continue
        depth, end = 1, m.end()
        for t in re.finditer(r"<(/?)span\b[^>]*>", fragment[m.end():]):
            depth += 1 if not t.group(1) else -1
            if depth == 0:
                end = m.end() + t.end()
                break
        out.append(fragment[i:m.start()])
        i = end
    out.append(fragment[i:])
    return "".join(out)


def blocks(doc: str, needle: str, is_regex: bool = False) -> list[str]:
    """Crude but adequate: slice from each opening <div ...needle...> to the
    div that closes it, by counting <div/</div> pairs."""
    out = []
    pattern = needle if is_regex else re.escape(needle)
    for m in re.finditer(r"<div[^>]*" + pattern + r"[^>]*>", doc):
        i = m.start()
        depth = 0
        for t in re.finditer(r"</?div\b[^>]*>", doc[i:]):
            depth += 1 if not t.group(0).startswith("</") else -1
            if depth == 0:
                out.append(doc[i:i + t.end()])
                break
    return out


def chapters_of(doc: str) -> list[tuple[str, str]]:
    out = []
    starts = [m.start() for m in re.finditer(r'<section class="chapter"', doc)]
    for n, i in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else doc.find("</main>", i)
        chunk = doc[i:end if end > 0 else len(doc)]
        found = re.search(r'id="([^"]+)"', chunk)
        out.append((found.group(1) if found else f"chapter {n + 1}", chunk))
    return out


# ── structural checks ─────────────────────────────────────────
def check_leftovers(doc: str, r: Report) -> None:
    for m in set(re.findall(r"\{\{[A-Z_]+\}\}", doc)):
        r.error(f"unfilled shell placeholder {m}")
    for m in set(re.findall(r"\bCH_[A-Z]+\b", doc)):
        r.error(f"unfilled scaffold placeholder {m}")
    todos = doc.count("TODO")
    if todos:
        r.error(f"{todos} TODO marker(s) left in the course — scaffolding was not filled in")


def check_ids(doc: str, r: Report) -> None:
    for cid, n in Counter(re.findall(r'\sid="([^"]+)"', doc)).items():
        if n > 1:
            r.error(f'duplicate id="{cid}" ({n} times) — lookups resolve to the first match only')


def check_no_inline_handlers(doc: str, r: Report) -> None:
    for m in set(re.findall(r'\bon(click|change|input|submit|mouseover)="', doc)):
        r.error(f'inline on{m} handler found — this engine wires everything by data-u attributes; '
                f"an inline handler means markup copied from somewhere else")


def check_parts(doc: str, r: Report) -> None:
    for name in set(re.findall(r'data-u="([^"]+)"', doc)):
        if name not in KNOWN_PARTS:
            r.error(f'data-u="{name}" is not a component course.js knows about '
                    f"(known: {', '.join(sorted(KNOWN_PARTS))})")


def check_gloss(doc: str, r: Report) -> None:
    targets = set(re.findall(r'popovertarget="([^"]+)"', doc))
    defined = set(re.findall(r'<span class="gloss-def"[^>]*\bid="([^"]+)"', doc))
    for t in sorted(targets - defined):
        r.error(f'a gloss points at popovertarget="{t}" but no .gloss-def with that id exists')
    for d in sorted(defined - targets):
        r.warn(f'gloss definition "{d}" is never opened by any term')
    for tag in re.findall(r"<span class=\"gloss-def\"[^>]*>", doc):
        if "popover" not in attrs_of(tag) and " popover" not in tag:
            r.error("a .gloss-def is missing the popover attribute — it will render inline as loose text")
    for tag in re.findall(r'<button class="gloss"[^>]*>', doc):
        if 'type="button"' not in tag:
            r.warn('a .gloss button has no type="button"')


def check_check(doc: str, r: Report) -> None:
    for i, block in enumerate(blocks(doc, 'data-u="check"'), 1):
        if "data-u-mark" not in block:
            r.error(f"check #{i} has no [data-u-mark] button — nothing can grade it")
        qs = re.findall(r"<div class=\"check__q\"[^>]*>", block)
        if not qs:
            r.error(f"check #{i} has no [data-u-question] blocks")
        for q in qs:
            a = attrs_of(q)
            correct = a.get("data-u-correct")
            if not correct:
                r.error(f"check #{i}: a question has no data-u-correct")
            if not a.get("data-u-if-right") or not a.get("data-u-if-wrong"):
                r.error(f"check #{i}: a question is missing data-u-if-right / data-u-if-wrong")
        answers = re.findall(r'data-u-answer="([^"]+)"', block)
        corrects = re.findall(r'data-u-correct="([^"]+)"', block)
        for c in corrects:
            if c not in answers:
                r.error(f'check #{i}: data-u-correct="{c}" matches no answer button')
        if "data-u-result" not in block:
            r.error(f"check #{i} has no [data-u-result] element to write feedback into")
        elif 'aria-live' not in block:
            r.warn(f"check #{i} result is not aria-live — screen readers will not announce it")


def check_trace(doc: str, r: Report) -> None:
    for i, block in enumerate(blocks(doc, 'data-u="trace"'), 1):
        m = re.search(r"data-u-steps='(.*?)'", block, re.S)
        if not m:
            r.error(f"trace #{i} has no data-u-steps")
            continue
        try:
            steps = json.loads(html_mod.unescape(m.group(1)))
        except Exception as e:
            r.error(f"trace #{i}: data-u-steps is not valid JSON ({e}) — an apostrophe inside the "
                    f"single-quoted attribute is the usual cause")
            continue
        nodes = set(re.findall(r'data-u-node="([^"]+)"', block))
        for s in steps:
            for key in ("at", "from", "to"):
                v = s.get(key)
                if v and v not in nodes:
                    r.error(f'trace #{i}: step {key}="{v}" names no node inside this trace '
                            f"(has: {', '.join(sorted(nodes)) or 'none'})")
            if bool(s.get("from")) != bool(s.get("to")):
                r.error(f"trace #{i}: a step has only one of from/to — a pulse needs both")
            if not s.get("say"):
                r.warn(f"trace #{i}: a step has no caption")
        if "data-u-pulse" not in block:
            r.warn(f"trace #{i} has no [data-u-pulse] element — steps will highlight but nothing moves")
        if "data-u-next" not in block:
            r.error(f"trace #{i} has no [data-u-next] button")


def check_thread(doc: str, r: Report) -> None:
    for i, block in enumerate(blocks(doc, 'data-u="thread"'), 1):
        msgs = re.findall(r"<div class=\"thread__msg\"[^>]*>", block)
        if len(msgs) < 2:
            r.error(f"thread #{i} has fewer than two messages")
        for msg in msgs:
            if "data-u-msg" not in msg:
                r.error(f"thread #{i}: a .thread__msg is missing data-u-msg and will never be revealed")
            if "hidden" not in msg:
                r.warn(f"thread #{i}: a message is not hidden initially — it will show before its turn")
        if "data-u-next" not in block:
            r.error(f"thread #{i} has no [data-u-next] button")


def check_match(doc: str, r: Report) -> None:
    for i, block in enumerate(blocks(doc, 'data-u="match"'), 1):
        chips = set(re.findall(r'data-u-chip="([^"]+)"', block))
        slots = re.findall(r'data-u-slot="([^"]+)"', block)
        if not chips or not slots:
            r.error(f"match #{i} needs both chips and slots")
        for s in slots:
            if s not in chips:
                r.error(f'match #{i}: slot "{s}" has no chip with that key — it can never be right')
        if "data-u-mark" not in block:
            r.error(f"match #{i} has no [data-u-mark] button")
        if "data-u-result" not in block:
            r.warn(f"match #{i} has no [data-u-result] — the learner gets no summary")


def check_hunt(doc: str, r: Report) -> None:
    for i, block in enumerate(blocks(doc, 'data-u="hunt"'), 1):
        lines = re.findall(r"<button class=\"hunt__line\"[^>]*>", block)
        bugs = [l for l in lines if 'data-u-line="bug"' in l]
        if len(bugs) != 1:
            r.error(f"hunt #{i} has {len(bugs)} lines marked as the bug — it needs exactly one")
        for l in lines:
            if not attrs_of(l).get("data-u-why"):
                r.warn(f"hunt #{i}: a line has no data-u-why, so a wrong guess teaches nothing")


def check_stack(doc: str, r: Report) -> None:
    for i, block in enumerate(blocks(doc, 'data-u="stack"'), 1):
        tabs = re.findall(r'data-u-tab="([^"]+)"', block)
        panes = re.findall(r'data-u-pane="([^"]+)"', block)
        for t in tabs:
            if t not in panes:
                r.error(f'stack #{i}: tab "{t}" has no matching [data-u-pane]')
        chosen = block.count('aria-selected="true"')
        if chosen != 1:
            r.error(f"stack #{i} has {chosen} tabs marked aria-selected=true — it needs exactly one")
        visible = len([p for p in re.findall(r"<div class=\"stack__pane\"[^>]*>", block) if "hidden" not in p])
        if visible != 1:
            r.error(f"stack #{i} shows {visible} panes at rest — all but one need the hidden attribute")


def check_rail(doc: str, r: Report) -> None:
    goto = re.findall(r'data-u-goto="([^"]+)"', doc)
    chapter_ids = [cid for cid, _ in chapters_of(doc)]
    if len(goto) != len(chapter_ids):
        r.error(f"{len(goto)} rail entries for {len(chapter_ids)} chapters")
    for g in goto:
        if g not in chapter_ids:
            r.error(f'rail entry points at #{g}, which is not a chapter in this page')


def check_figures(doc: str, r: Report) -> None:
    left = re.findall(r'data-figure="([\w-]+)"', doc)
    for name in sorted(set(left)):
        r.error(f'figure "{name}" was never rendered — the placeholder must be exactly '
                f'<div class="figure" data-figure="{name}"></div> and the spec must exist '
                f"in diagrams/{name}.json")

    total = count_blocks(doc, "figure")
    if total == 0:
        r.warn("the course has no diagrams — most systems have at least one shape "
               "(who talks to whom, what order, what depends on what) that a picture carries "
               "better than a paragraph")
    for svg in re.findall(r"<svg[^>]*>", doc):
        if 'role="img"' not in svg or "aria-labelledby" not in svg:
            r.error("a diagram is missing role=img and aria-labelledby, so it is invisible "
                    "to a screen reader")
    for fig in blocks(doc, r'class="figure[ "]', is_regex=True):
        if "figure__alt" not in fig:
            r.warn("a diagram has no described-in-words alternative")

    for cid, chunk in chapters_of(doc):
        n = count_blocks(chunk, "figure")
        if n > 2:
            r.warn(f"{cid}: {n} diagrams — more than two in one chapter usually means one of "
                   f"them is decoration")


def check_a11y(doc: str, r: Report) -> None:
    if not re.search(r"<html[^>]+lang=", doc):
        r.error("<html> has no lang attribute")
    for img in re.findall(r"<img[^>]*>", doc):
        if "alt=" not in img:
            r.error("an <img> has no alt attribute")
    for b in re.findall(r"<button[^>]*>\s*</button>", doc):
        r.error("an empty <button> has no accessible name")
    css = Path("course.css")
    if css.exists() and "prefers-reduced-motion" not in css.read_text(encoding="utf-8"):
        r.warn("course.css has no prefers-reduced-motion block")


# ── content checks ────────────────────────────────────────────
def check_content(doc: str, r: Report) -> None:
    chapters = chapters_of(doc)
    if not chapters:
        r.error("no chapters found")
        return

    total_code = 0
    for cid, chunk in chapters:
        if 'data-u="check"' not in chunk:
            r.error(f"{cid}: no check — every chapter ends by asking the reader to think")
        if not any(mark in chunk for mark in INTERACTIVE_MARKERS) \
                and not any(has_block(chunk, b) for b in ("defend", "depth", "fieldwork", "recall")):
            r.error(f"{cid}: nothing interactive")

        gloss = chunk.count('class="gloss"')
        if gloss == 0:
            r.error(f"{cid}: no inline definitions — non-technical readers need them")

        # Two kinds of text are not expository prose and are exempt from the
        # prose budgets: a figure's generated text alternative (complete by
        # design — nine diagram steps are nine sentences), and recall prompts
        # (an after-reading activity whose questions must stay visible).
        prose = re.sub(r"<figure\b.*?</figure>", " ", chunk, flags=re.S)
        for exempt in blocks(prose, r'class="recall[ "]', is_regex=True):
            prose = prose.replace(exempt, " ")
        surface = re.sub(r"<details\b.*?</details>", " ", prose, flags=re.S)

        # ── the depth floor ────────────────────────────────────────
        # A reader who was never challenged cannot defend anything. These are
        # minimums; the ceilings below are maximums. Both apply at once.
        if not has_block(chunk, "defend"):
            r.error(f"{cid}: no objection to answer — a chapter that is never challenged "
                    f"produces the feeling of understanding without the substance")
        if not has_block(chunk, "depth"):
            r.warn(f"{cid}: no layered explanation — without a mechanism layer this chapter "
                   f"tells the reader what happens but not how")

        # ── the complexity budget ──────────────────────────────────
        # Extraneous load is what makes a course feel hard. These ceilings
        # exist because adding material is the easy mistake, not omitting it.
        interactive = sum(chunk.count(m) for m in INTERACTIVE_MARKERS)
        if interactive > 4:
            r.warn(f"{cid}: {interactive} interactive parts — above about four a chapter starts to "
                   f"read as a dashboard rather than an explanation")
        if gloss > 7:
            r.warn(f"{cid}: {gloss} new terms defined — more than about seven in one chapter is "
                   f"more vocabulary than anyone absorbs in a sitting")
        code = len(blocks(chunk, r'class="annotated[ "]', is_regex=True))
        total_code += code
        if code > 2:
            r.warn(f"{cid}: {code} code passages — two is usually the most a chapter can carry")
        total_words = len(text_of(without_gloss(prose)).split())
        surface_words = len(text_of(without_gloss(surface)).split())
        if surface_words > 800:
            r.warn(f"{cid}: about {surface_words} words visible before anything is expanded — "
                   f"move some of it behind a depth layer rather than cutting it")
        depth_share = (total_words - surface_words) / total_words if total_words else 0
        if total_words > 400 and depth_share < 0.15:
            r.warn(f"{cid}: only {depth_share:.0%} of the words sit behind a depth layer — "
                   f"a chapter this size usually has mechanism worth folding away")

        # Three sentences is a rule about the scannable surface. Inside a layer
        # the reader chose to open, sustained explanation is the whole point —
        # so it is held to a looser limit rather than the same one.
        para_re = r"<p(?:\s[^>]*)?>(.*?)</p>"
        surface_paras = re.findall(para_re, surface, re.S)
        longs = [p for p in surface_paras
                 if len(SENTENCE_RE.findall(text_of(without_gloss(p)))) > 3]
        if longs:
            r.warn(f"{cid}: {len(longs)} paragraph(s) on the surface run past three sentences — "
                   f"turn one into a visual, or fold it into a depth layer")
        folded = "".join(re.findall(r"<details\b.*?</details>", prose, flags=re.S))
        rambling = [p for p in re.findall(para_re, folded, re.S)
                    if len(SENTENCE_RE.findall(text_of(without_gloss(p)))) > 6]
        if rambling:
            r.warn(f"{cid}: {len(rambling)} paragraph(s) inside a depth layer run past six "
                   f"sentences — even opted-in prose needs paragraph breaks")
        visuals = sum(chunk.count(f'"{m}') + chunk.count(f'="{m}"') for m in VISUAL_MARKERS)
        paras = surface_paras
        if paras and visuals and len(paras) / visuals > 4:
            r.warn(f"{cid}: {len(paras)} paragraphs against {visuals} visual blocks — reads like a textbook")

    # A reader who is never shown the whole territory cannot tell known-unknowns
    # from unknown-unknowns, and finishes feeling the system is boundless.
    if not has_block(doc, "territory"):
        r.error("the course never maps the territory — every area of the system must be named "
                "once, with what this course covers marked and the rest routed to later courses")
    else:
        first = chapters[0][1] if chapters else ""
        if not has_block(first, "territory"):
            r.warn("the territory map is not in chapter 1 — it works as an advance organizer, "
                   "which means it belongs before the journey starts")
        for t in blocks(doc, r'class="territory[ "]', is_regex=True):
            rows = count_blocks(t, "territory__row")
            here = t.count("territory__status--here")
            if rows and not here:
                r.error("the territory map marks nothing as covered by this course")
            if rows and here == rows:
                r.error("the territory map claims this course covers everything — on any real "
                        "system that is not honesty, it is the absence of a map")

        covered = []
        for t in blocks(doc, r'class="territory[ "]', is_regex=True):
            for row in re.finditer(r'<div class="territory__row">(.*?)</div>', t, re.S):
                if "--here" in row.group(1):
                    name = re.search(r'class="territory__name">\s*([\w-]+)', row.group(1))
                    if name:
                        covered.append(name.group(1))
        stripped = doc
        for t in blocks(doc, r'class="territory[ "]', is_regex=True):
            stripped = stripped.replace(t, " ")
        for name in covered:
            if not re.search(re.escape(name), stripped, re.I):
                r.warn(f'the territory marks "{name}" as covered by this course, but the name '
                       f"never appears again — a claim of coverage the chapters do not visibly keep")

    # Reading about a codebase is not contact with it. Fieldwork sends the
    # reader into the real repository with a prediction to check.
    fieldwork = blocks(doc, r'class="fieldwork[ "]', is_regex=True)
    if len(fieldwork) < 2:
        r.error(f"the course has {len(fieldwork)} fieldwork exercise(s) — it needs at least two "
                f"that send the reader into the actual repository to predict and then check")
    for i, fw in enumerate(fieldwork, 1):
        if "Predict" not in fw and "predict" not in fw:
            r.warn(f"fieldwork #{i} has no predict step — without a written prediction the check "
                   f"is just more reading")
        if "fieldwork__check" not in fw:
            r.error(f"fieldwork #{i} has no folded check — the answer must be hidden until "
                    f"the reader has been to the repository")

    # One exposure decays. The course must end with retrieval prompts meant to
    # be re-taken after days, not recognition questions answered once.
    if not has_block(doc, "recall"):
        r.error("the course has no recall section — without retrieval prompts to re-take after "
                "days, everything read here follows the forgetting curve")
    else:
        last = chapters[-1][1] if chapters else ""
        if not has_block(last, "recall"):
            r.warn("the recall section is not in the final chapter — it should be the last "
                   "thing the reader meets")
        for rc in blocks(doc, r'class="recall[ "]', is_regex=True):
            n = count_blocks(rc, "recall__item")
            if n < 4:
                r.warn(f"only {n} recall prompt(s) — one per chapter plus one for the whole "
                       f"journey is the floor")

    tradeoffs = count_blocks(doc, "tradeoff")
    if tradeoffs < 3:
        r.error(f"the course records {tradeoffs} design decision(s) — defending a system means "
                f"knowing what was rejected and what the choice cost; find at least three, "
                f"in the decision records, the commit history or the code comments")
    unsourced = sum(1 for b in blocks(doc, r'class="tradeoff[ "]', is_regex=True)
                    if "tradeoff__src" not in b)
    if unsourced:
        r.error(f"{unsourced} decision card(s) cite no source — rationale that is not in the "
                f"repository is rationale you invented, and it will not survive a question")

    if total_code < 2:
        r.error(f"the course shows real code {total_code} time(s) — it needs at least two passages, "
                f"though not every chapter needs one")
    if len(chapters) > 6:
        r.warn(f"{len(chapters)} chapters — more thin chapters is worse than fewer thick ones")

    whole = text_of(doc).lower()
    for word in TIRED_METAPHORS:
        n = whole.count(word)
        if n > 1:
            r.warn(f'the "{word}" metaphor appears {n} times — each concept deserves its own')

    kinds = {m.split('"')[1] for m in INTERACTIVE_MARKERS if m in doc}
    if len(kinds) < 2:
        r.warn("the course uses only one kind of interactive part — variety helps, "
               "though never add one that has nothing to teach")

    corrects = re.findall(r'data-u-correct="([^"]+)"', doc)
    if len(corrects) >= 4 and len(set(corrects)) == 1:
        r.warn(f'every question\'s correct answer is "{corrects[0]}" — vary the position')


# ── code fidelity ─────────────────────────────────────────────
def check_code_fidelity(doc: str, src: Path, r: Report) -> None:
    if not src.is_dir():
        r.error(f"--src {src} is not a directory")
        return

    haystack: dict[Path, list[str]] = {}
    for p in src.rglob("*"):
        if not p.is_file() or ".git" in p.parts:
            continue
        if p.stat().st_size > 2_000_000:
            continue
        try:
            haystack[p] = [l.rstrip() for l in
                           p.read_text(encoding="utf-8", errors="ignore").splitlines()]
        except OSError:
            continue

    def find_seq(lines: list[str], seq: list[str]) -> int | None:
        for k in range(len(lines) - len(seq) + 1):
            if lines[k:k + len(seq)] == seq:
                return k + 1
        return None

    # Citations rot silently: the snippet can still exist while "lines 6-11"
    # points at something else after the file moves. Check both.
    cite_re = re.compile(r'class="annotated__file">\s*(.*?)\s*<')
    for block in blocks(doc, r'class="annotated[ "]', is_regex=True):
        m = cite_re.search(block)
        if not m:
            continue
        cite = text_of(m.group(1))
        parts = re.match(r"^(.*?),\s*lines?\s+(\d+)\s*[-–]\s*(\d+)\s*$", cite)
        if not parts:
            r.warn(f'citation "{cite}" names no line numbers — a reader cannot find the passage')
            continue
        rel, a, b = parts.group(1).strip(), int(parts.group(2)), int(parts.group(3))
        target = src / rel
        if not target.exists():
            r.error(f'citation points at {rel}, which does not exist under {src} — the file moved '
                    f"or was renamed, and the course is now describing something that is not there")
            continue
        pre = re.search(r"<pre><code>(.*?)</code></pre>", block, re.S)
        if not pre:
            continue
        snippet = [html_mod.unescape(TAG_RE.sub("", l)).rstrip()
                   for l in spans_of_class(pre.group(1), "cl")]
        while snippet and not snippet[0].strip():
            snippet.pop(0)
        while snippet and not snippet[-1].strip():
            snippet.pop()
        actual = [l.rstrip("\n").rstrip() for l in
                  target.read_text(encoding="utf-8", errors="ignore").splitlines()]
        if snippet == actual[a - 1:a - 1 + len(snippet)]:
            if len(snippet) != b - a + 1:
                r.warn(f"{rel}: the citation says lines {a}-{b} but the snippet is "
                       f"{len(snippet)} line(s) — say lines {a}-{a + len(snippet) - 1}")
            continue
        found = None
        for k in range(len(actual) - len(snippet) + 1):
            if actual[k:k + len(snippet)] == snippet:
                found = k + 1
                break
        if found:
            r.error(f"{rel}: cited as lines {a}-{b} but the passage now sits at lines "
                    f"{found}-{found + len(snippet) - 1} — the code moved; update the citation")
        # not found at all is already reported by the verbatim check below

    # Fieldwork sends a reader to a path; a renamed path strands them there.
    for i, fw in enumerate(blocks(doc, r'class="fieldwork[ "]', is_regex=True), 1):
        for token in re.findall(r"<code>([^<\s]+)</code>", fw):
            if "/" not in token:
                continue
            if not (src / token.rstrip("/")).exists():
                r.error(f"fieldwork #{i} sends the reader to {token}, which does not exist "
                        f"under {src}")

    checked = matched = 0
    for block in blocks(doc, r'class="annotated[ "]', is_regex=True):
        pre = re.search(r"<pre><code>(.*?)</code></pre>", block, re.S)
        if not pre:
            continue
        lines = [html_mod.unescape(TAG_RE.sub("", l)).rstrip()
                 for l in spans_of_class(pre.group(1), "cl")]
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        meaningful = [l for l in lines if l.strip()]
        if len(meaningful) < 2:
            continue
        checked += 1
        where = re.search(r'class="annotated__file">(.*?)<', block)
        label = text_of(where.group(1)) if where else "(no file noted)"

        # whole lines must match — substring search would let a snippet whose
        # last line is a prefix of the real line (a dropped semicolon) pass
        found = any(find_seq(body, lines) is not None for body in haystack.values())
        if not found:
            loose = [l.strip() for l in meaningful]
            found = any(find_seq([b.strip() for b in body], loose) is not None
                        for body in haystack.values())
            if found:
                r.warn(f"code snippet ({label}) matches the source only after re-indenting — "
                       f"paste it exactly as it appears in the file")
        if found:
            matched += 1
        else:
            r.error(f"code snippet ({label}) does not appear verbatim in {src} — "
                    f"first line: {meaningful[0].strip()[:60]!r}")

    r.note(f"code fidelity: {matched}/{checked} snippets found verbatim in {src}")


# ── main ──────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="index.html")
    ap.add_argument("--src", default=None, help="path to the codebase being taught")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"verify: {path} not found — run `python3 build.py` first", file=sys.stderr)
        return 1
    raw = path.read_text(encoding="utf-8")
    doc = markup_only(raw)
    inlined = len(raw) - len(doc) > 2000

    r = Report()
    for fn in (check_leftovers, check_ids, check_no_inline_handlers, check_parts, check_gloss,
               check_check, check_trace, check_thread, check_match, check_hunt, check_stack,
               check_rail, check_figures, check_a11y, check_content):
        fn(doc, r)
    if args.src:
        check_code_fidelity(doc, Path(args.src), r)

    for label, items in (("ERROR", r.errors), ("WARN", r.warns), ("NOTE", r.notes)):
        for item in items:
            print(f"{label:5} {item}")

    n_ch = len(chapters_of(doc))
    print()
    if inlined:
        print(f"(self-contained build: {(len(raw) - len(doc)) // 1024} KB of inlined "
              f"stylesheet and engine were skipped)")
    if r.errors or (args.strict and r.warns):
        print(f"✗ {len(r.errors)} error(s), {len(r.warns)} warning(s) across {n_ch} chapters.")
        return 1
    print(f"✓ verified — {n_ch} chapters, {len(r.warns)} warning(s), no errors.")
    return 0


if __name__ == "__main__":
    # Windows consoles default to a legacy code page that cannot encode the
    # check marks and dashes in our output; never let printing crash a run.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    raise SystemExit(main())
