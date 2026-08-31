#!/usr/bin/env python3
"""Render diagram specs to inline SVG at build time.

No runtime library and no network: a course keeps working offline, in print,
and with JavaScript switched off. Five shapes, each answering one kind of
question:

    flow      what talks to what            (C4 context / container)
    sequence  what happens in what order, and who waits
    layers    what is allowed to depend on what
    states    what states a thing can be in, and what moves it
    bars      how big, compared with what

Two rules are enforced by construction rather than left to the author:

  * Labels sit on the thing they name. There are no legends and no keys —
    a meta-analysis of 58 comparisons puts the cost of separating them at
    g = 0.63, which is a large effect to pay for tidiness.
  * Every figure carries a title, a description and a text alternative, so
    the content survives for a screen reader and for anyone who cannot see
    the picture.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

# One coordinate space for every figure; CSS scales it to the column.
W = 900
PAD = 24
CHAR = 7.4          # approximate advance of the label font at 13px
LINE = 18


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def text_width(label: str, char: float = CHAR) -> float:
    return len(str(label)) * char


def wrap(label: str, limit: int) -> list[str]:
    words, lines, line = str(label).split(), [], ""
    for w in words:
        candidate = f"{line} {w}".strip()
        if len(candidate) > limit and line:
            lines.append(line)
            line = w
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines or [""]


def defs(uid: str) -> str:
    return (
        f'<defs>'
        f'<marker id="{uid}-tip" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" class="fig-arrowhead"/></marker>'
        f'</defs>'
    )


def frame(uid: str, spec: dict, height: float, body: str, width: float = W) -> str:
    """Wrap the drawing in an accessible, themed <svg>."""
    title, desc = esc(spec.get("title", "")), esc(spec.get("desc", ""))
    return (
        f'<svg class="fig" viewBox="0 0 {int(width)} {int(height)}" role="img" '
        f'aria-labelledby="{uid}-t {uid}-d" preserveAspectRatio="xMidYMid meet">'
        f'<title id="{uid}-t">{title}</title><desc id="{uid}-d">{desc}</desc>'
        f'{defs(uid)}<g aria-hidden="true">{body}</g></svg>'
    )


def box(x, y, w, h, label, note=None, kind="node") -> str:
    lines = wrap(label, max(8, int(w / CHAR) - 2))
    total = len(lines) * LINE + (LINE if note else 0)
    ty = y + h / 2 - total / 2 + LINE * 0.75
    out = [f'<rect class="fig-{kind}" x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" '
           f'height="{h:.0f}" rx="10"/>']
    for line in lines:
        out.append(f'<text class="fig-label" x="{x + w / 2:.0f}" y="{ty:.0f}" '
                   f'text-anchor="middle">{esc(line)}</text>')
        ty += LINE
    if note:
        out.append(f'<text class="fig-note" x="{x + w / 2:.0f}" y="{ty:.0f}" '
                   f'text-anchor="middle">{esc(note)}</text>')
    return "".join(out)


def arrow(x1, y1, x2, y2, uid, dashed=False) -> str:
    cls = "fig-edge fig-edge--dashed" if dashed else "fig-edge"
    return (f'<line class="{cls}" x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" '
            f'y2="{y2:.0f}" marker-end="url(#{uid}-tip)"/>')


# ── flow ──────────────────────────────────────────────────────────
def render_flow(spec: dict, uid: str) -> tuple[str, float, list[str]]:
    nodes = spec["nodes"]
    edges = spec.get("edges", [])
    zones = spec.get("zones", [])
    n = len(nodes)

    # The gap has to hold the widest edge label, or labels sit on the boxes.
    widest = max([text_width(e.get("label", ""), 6.4) for e in edges] or [0])
    gap = max(46, widest + 22)
    zone_pad = 14
    bw = 150
    breaks = sum(1 for i in range(n - 1)
                 if next((z for z in zones if nodes[i]["id"] in z["nodes"]), None)
                 is not next((z for z in zones if nodes[i + 1]["id"] in z["nodes"]), None))
    needed = 2 * PAD + 2 * zone_pad * bool(zones) + n * bw + (n - 1) * gap + breaks * zone_pad * 2
    canvas = max(W, needed)
    if canvas == W:                       # room to spare: spread the boxes out
        bw = (W - 2 * PAD - 2 * zone_pad * bool(zones) - (n - 1) * gap - breaks * zone_pad * 2) / n
    bh = 88
    top = PAD + (30 if zones else 0)

    at, x = {}, (PAD + zone_pad) if zones else PAD
    for i, node in enumerate(nodes):
        at[node["id"]] = (x, top, bw, bh)
        x += bw + gap
        # a zone boundary between this node and the next costs a little padding
        if zones and i + 1 < n:
            here = next((z for z in zones if node["id"] in z["nodes"]), None)
            nxt = next((z for z in zones if nodes[i + 1]["id"] in z["nodes"]), None)
            if here is not nxt:
                x += zone_pad * 2

    out = []
    for zone in zones:
        members = [at[i] for i in zone["nodes"] if i in at]
        if not members:
            continue
        zx = min(m[0] for m in members) - zone_pad
        zw = max(m[0] + m[2] for m in members) - zx + zone_pad
        out.append(f'<rect class="fig-zone" x="{zx:.0f}" y="{top - zone_pad:.0f}" '
                   f'width="{zw:.0f}" height="{bh + zone_pad * 2:.0f}" rx="14"/>')
        # Clip the label to its own zone so neighbouring labels cannot collide.
        room = int(zw / 6.2)
        label = zone["label"] if len(zone["label"]) <= room else zone["label"][:max(3, room - 1)] + "…"
        out.append(f'<text class="fig-zone-label" x="{zx + 4:.0f}" '
                   f'y="{top - zone_pad - 8:.0f}">{esc(label)}</text>')

    for node in nodes:
        x, y, w, h = at[node["id"]]
        out.append(box(x, y, w, h, node["label"], node.get("note")))

    alt = []
    for edge in edges:
        (x1, y1, w1, _), (x2, y2, w2, _) = at[edge["from"]], at[edge["to"]]
        mid = y1 + bh / 2
        if x2 > x1:
            sx, ex = x1 + w1 + 5, x2 - 9
        else:
            sx, ex = x1 - 5, x2 + w2 + 9
        out.append(arrow(sx, mid, ex, mid, uid, edge.get("dashed")))
        if edge.get("label"):
            out.append(f'<text class="fig-edge-label" x="{(sx + ex) / 2:.0f}" '
                       f'y="{mid - 12:.0f}" text-anchor="middle">{esc(edge["label"])}</text>')
        alt.append(f'{edge["from"]} → {edge["to"]}'
                   + (f' ({edge["label"]})' if edge.get("label") else ""))

    height = top + bh + zone_pad + PAD
    words = [f'{nd["label"]}' + (f' — {nd["note"]}' if nd.get("note") else "") for nd in nodes]
    return ("".join(out), height,
            ["Parts: " + "; ".join(words)] + (["Links: " + "; ".join(alt)] if alt else []),
            canvas)


# ── sequence ──────────────────────────────────────────────────────
def render_sequence(spec: dict, uid: str) -> tuple[str, float, list[str]]:
    lanes = spec["lanes"]
    steps = spec["steps"]
    n = len(lanes)
    head_h = 52
    step_gap = 54
    lane_w = (W - 2 * PAD) / n
    cx = {lane["id"]: PAD + lane_w * i + lane_w / 2 for i, lane in enumerate(lanes)}

    body_top = PAD + head_h + 18
    height = body_top + step_gap * len(steps) + PAD

    out = []
    for i, lane in enumerate(lanes):
        x = PAD + lane_w * i
        out.append(box(x + 6, PAD, lane_w - 12, head_h, lane["label"], kind="lane-head"))
        out.append(f'<line class="fig-lifeline" x1="{cx[lane["id"]]:.0f}" y1="{PAD + head_h:.0f}" '
                   f'x2="{cx[lane["id"]]:.0f}" y2="{height - PAD:.0f}"/>')

    alt = []
    y = body_top + 10
    for idx, step in enumerate(steps, 1):
        if step.get("note") and step.get("at"):
            x = cx[step["at"]]
            lines = wrap(step["note"], 26)
            w = max(text_width(max(lines, key=len)) + 26, 120)
            h = len(lines) * LINE + 16
            out.append(f'<rect class="fig-selfnote" x="{x - w / 2:.0f}" y="{y - h / 2:.0f}" '
                       f'width="{w:.0f}" height="{h:.0f}" rx="8"/>')
            ty = y - h / 2 + LINE
            for line in lines:
                out.append(f'<text class="fig-note" x="{x:.0f}" y="{ty:.0f}" '
                           f'text-anchor="middle">{esc(line)}</text>')
                ty += LINE
            alt.append(f'{idx}. at {step["at"]}: {step["note"]}')
        else:
            x1, x2 = cx[step["from"]], cx[step["to"]]
            direction = 1 if x2 > x1 else -1
            out.append(arrow(x1 + 6 * direction, y, x2 - 10 * direction, y, uid, step.get("dashed")))
            if step.get("label"):
                out.append(f'<text class="fig-edge-label" x="{(x1 + x2) / 2:.0f}" y="{y - 9:.0f}" '
                           f'text-anchor="middle">{esc(step["label"])}</text>')
            alt.append(f'{idx}. {step["from"]} → {step["to"]}'
                       + (f': {step["label"]}' if step.get("label") else ""))
        y += step_gap

    return "".join(out), height, ["Order: " + " ".join(alt)]


# ── layers ────────────────────────────────────────────────────────
def render_layers(spec: dict, uid: str) -> tuple[str, float, list[str]]:
    layers = spec["layers"]
    n = len(layers)
    header = 46          # room for a band's own label and note
    inset = 22           # how far each band sits inside the one outside it
    floor_h = 40         # breathing room inside the innermost band
    arrow_gutter = 120   # right-hand column reserved for the dependency arrow

    height = PAD * 2 + header * n + floor_h
    out, alt = [], []
    for i, layer in enumerate(layers):
        x = PAD + inset * i
        y = PAD + header * i
        w = W - 2 * PAD - inset * 2 * i - (arrow_gutter if i == 0 else 0)
        h = height - y - PAD          # every band reaches the same floor
        out.append(f'<rect class="fig-band fig-band--{i}" x="{x:.0f}" y="{y:.0f}" '
                   f'width="{w:.0f}" height="{h:.0f}" rx="14"/>')
        out.append(f'<text class="fig-band-label" x="{x + 16:.0f}" y="{y + 22:.0f}">'
                   f'{esc(layer["label"])}</text>')
        if layer.get("note"):
            note = layer["note"]
            room = int((w - 32) / 6.2)
            if len(note) > room:
                note = note[:max(3, room - 1)] + "…"
            out.append(f'<text class="fig-note" x="{x + 16:.0f}" y="{y + 39:.0f}">'
                       f'{esc(note)}</text>')
        alt.append(f'{layer["label"]}' + (f' — {layer["note"]}' if layer.get("note") else ""))

    if spec.get("arrow", "inward") == "inward":
        ax = W - PAD - 34
        out.append(arrow(ax, PAD + 30, ax, PAD + header * (n - 1) + 24, uid))
        out.append(f'<text class="fig-edge-label" x="{ax - 12:.0f}" y="{PAD + 22:.0f}" '
                   f'text-anchor="end">{esc(spec.get("arrowLabel", "depends on"))}</text>')

    return "".join(out), height, ["Outermost first: " + " → ".join(alt),
                                  spec.get("arrowLabel", "Dependencies point inward").capitalize() + "."]


# ── states ────────────────────────────────────────────────────────
def render_states(spec: dict, uid: str) -> tuple[str, float, list[str]]:
    states = spec["states"]
    order = {st["id"]: i for i, st in enumerate(states)}
    n = len(states)
    transitions = spec.get("transitions", [])

    # Arcs need headroom above and below the row of states.
    arcs_above = [t for t in transitions if order[t["to"]] - order[t["from"]] > 1]
    arcs_below = [t for t in transitions if order[t["to"]] < order[t["from"]]]
    head = 30 + 34 * len(arcs_above)
    foot = 30 + 34 * len(arcs_below)

    gap = 46
    bw = min(170, (W - 2 * PAD - gap * (n - 1)) / n)
    bh = 56
    top = head
    at, x = {}, PAD + max(0, (W - 2 * PAD - (bw * n + gap * (n - 1))) / 2)
    out = []
    for st in states:
        at[st["id"]] = (x, top, bw, bh)
        out.append(box(x, top, bw, bh, st["label"],
                       kind="state-final" if st.get("final") else "state"))
        x += bw + gap

    alt, up, down = [], 0, 0
    for tr in transitions:
        (x1, _, w1, _), (x2, _, w2, _) = at[tr["from"]], at[tr["to"]]
        step = order[tr["to"]] - order[tr["from"]]
        if step == 1:
            sx, ex = x1 + w1 + 5, x2 - 9
            out.append(arrow(sx, top + bh / 2, ex, top + bh / 2, uid))
            lx, ly = (sx + ex) / 2, top + bh / 2 - 12
        elif step > 1:
            up += 1
            lift = top - 16 - 34 * up
            sx, ex = x1 + w1 / 2, x2 + w2 / 2
            out.append(f'<path class="fig-edge" d="M {sx:.0f} {top - 4:.0f} '
                       f'C {sx:.0f} {lift:.0f}, {ex:.0f} {lift:.0f}, {ex:.0f} {top - 8:.0f}" '
                       f'marker-end="url(#{uid}-tip)"/>')
            lx, ly = (sx + ex) / 2, lift + 6
        else:
            down += 1
            drop = top + bh + 16 + 34 * down
            sx, ex = x1 + w1 / 2, x2 + w2 / 2
            out.append(f'<path class="fig-edge" d="M {sx:.0f} {top + bh + 4:.0f} '
                       f'C {sx:.0f} {drop:.0f}, {ex:.0f} {drop:.0f}, {ex:.0f} {top + bh + 8:.0f}" '
                       f'marker-end="url(#{uid}-tip)"/>')
            lx, ly = (sx + ex) / 2, drop + 14
        if tr.get("label"):
            out.append(f'<text class="fig-edge-label" x="{lx:.0f}" y="{ly:.0f}" '
                       f'text-anchor="middle">{esc(tr["label"])}</text>')
        alt.append(f'{tr["from"]} → {tr["to"]}' + (f' when {tr["label"]}' if tr.get("label") else ""))

    return "".join(out), top + bh + foot, [
        "States: " + ", ".join(s["label"] for s in states),
        "Moves: " + "; ".join(alt)]


# ── bars ──────────────────────────────────────────────────────────
def render_bars(spec: dict, uid: str) -> tuple[str, float, list[str]]:
    bars = spec["bars"]
    unit = spec.get("unit", "")
    label_w = max(text_width(b["label"]) for b in bars) + 24
    track = W - 2 * PAD - label_w - 90
    top = PAD
    row = 40
    peak = max(b["value"] for b in bars) or 1

    out, alt = [], []
    for i, b in enumerate(bars):
        y = top + i * row
        w = track * (b["value"] / peak)
        cls = "fig-bar fig-bar--lead" if b.get("highlight") else "fig-bar"
        out.append(f'<text class="fig-label" x="{PAD + label_w - 12:.0f}" y="{y + 21:.0f}" '
                   f'text-anchor="end">{esc(b["label"])}</text>')
        out.append(f'<rect class="{cls}" x="{PAD + label_w:.0f}" y="{y + 6:.0f}" '
                   f'width="{max(w, 2):.0f}" height="20" rx="4"/>')
        out.append(f'<text class="fig-value" x="{PAD + label_w + max(w, 2) + 10:.0f}" '
                   f'y="{y + 21:.0f}">{esc(b.get("display", b["value"]))}</text>')
        alt.append(f'{b["label"]}: {b.get("display", b["value"])}')

    return "".join(out), top + row * len(bars) + PAD, [
        (f"Measured in {unit}. " if unit else "") + "; ".join(alt)]


RENDERERS = {
    "flow": render_flow,
    "sequence": render_sequence,
    "layers": render_layers,
    "states": render_states,
    "bars": render_bars,
}


def render(spec: dict, name: str) -> str:
    kind = spec.get("type")
    if kind not in RENDERERS:
        raise ValueError(f"unknown figure type {kind!r} — choose from {', '.join(RENDERERS)}")
    for required in ("title", "desc"):
        if not spec.get(required):
            raise ValueError(f'figure "{name}" has no {required}; every figure needs one so it '
                             f"is described for a reader who cannot see it")
    uid = "fig-" + name
    drawn = RENDERERS[kind](spec, uid)
    body, height, alt = drawn[0], drawn[1], drawn[2]
    width = drawn[3] if len(drawn) > 3 else W
    svg = frame(uid, spec, height, body, width)
    caption = spec.get("caption", spec["title"])
    alt_text = " ".join(alt)
    return (
        f'<figure class="figure u-reveal">{svg}'
        f'<figcaption class="figure__caption">{esc(caption)}</figcaption>'
        f'<details class="figure__alt"><summary>Described in words</summary>'
        f'<p>{esc(spec["desc"])} {esc(alt_text)}</p></details>'
        f'</figure>'
    )


def load(course_root: Path, name: str) -> dict:
    path = course_root / "diagrams" / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f'no diagram named "{name}" — expected {path}')
    return json.loads(path.read_text(encoding="utf-8"))
