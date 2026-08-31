# The parts

Every part is wired by `data-u` attributes and initialised automatically. There
are no handler functions to call and no `onclick` anywhere — if you are writing
one, the markup came from somewhere that is not this project.

Do not copy markup from this page. Run `python3 scaffold.py chapter …` and get
the wiring for free; this page is here so you understand what you were given.

## Contract at a glance

| Part | Container | Must contain |
|---|---|---|
| `check` | `data-u="check"` | `[data-u-question]` with `data-u-correct`, `data-u-if-right`, `data-u-if-wrong`; buttons with `data-u-answer`; a `[data-u-result]`; a `[data-u-mark]` |
| `trace` | `data-u="trace"` + `data-u-steps='[…]'` | `[data-u-node="name"]` per actor, `[data-u-pulse]`, `[data-u-caption]`, `[data-u-next]` |
| `thread` | `data-u="thread"` | two or more `[data-u-msg]`, each `hidden`, each with `[data-u-who]`; `[data-u-next]` |
| `match` | `data-u="match"` | `[data-u-chip="key"]` and `[data-u-slot="key"]` that use the same keys; `[data-u-mark]` |
| `hunt` | `data-u="hunt"` | `[data-u-line="ok"]` several, `[data-u-line="bug"]` exactly one, each with `data-u-why` |
| `map` | `data-u="map"` | `[data-u-part="description"]` buttons, one `[data-u-readout]` |
| `stack` | `data-u="stack"` | `[data-u-tab="k"]` and `[data-u-pane="k"]` pairs; one tab `aria-selected="true"`, all other panes `hidden` |
| `gloss` | `button.gloss[popovertarget]` | a `span.gloss-def[popover]` with that id |

`annotated`, `aside`, `cards`, `steps`, `rows`, `tree` and `beat` are markup
only — no JavaScript, nothing to wire. So are the three learning-schedule parts:

| Part | Purpose | Must contain |
|---|---|---|
| `territory` | bound the whole system in chapter 1 | one `.territory__row` per area with a status chip: `--here`, `--next` or `--later`; at least one `--here` and at least one that is not |
| `fieldwork` | send the reader into the repository | an Open step, a Predict step, and the answer folded in `.fieldwork__check` |
| `recall` | retrieval prompts for later re-takes | four or more `.recall__item`s, answers folded, a note saying when to return |

## Diagrams

Diagrams are data, not markup. Put a spec in `diagrams/<name>.json` and
reference it from a chapter with exactly:

```html
<div class="figure" data-figure="request-lifecycle"></div>
```

`build.py` turns it into inline SVG. No library, no network, no script — the
picture survives print, offline reading and JavaScript being off. Start one
with `python3 scaffold.py figure sequence request-lifecycle`.

Pick the shape by the question it answers, not by which looks nicest:

| Question the reader has | Shape |
|---|---|
| What talks to what? | `flow` — boxes, arrows, optional zones |
| What happens in what order, and who waits? | `sequence` — lanes and messages |
| What is allowed to depend on what? | `layers` — nested bands, one inward arrow |
| What states can this be in, and what moves it? | `states` |
| How big is this compared with that? | `bars` |

Rules the renderer applies for you, and that you should not fight:

- **Every label sits on the thing it names.** There are no legends and no keys.
  The meta-analysis on this puts the cost of separating a label from its
  referent at g = 0.63, which is far too large to pay for a tidier picture.
- **Every figure needs a `title` and a `desc`**, and the build fails without
  them. The description is read to anyone who cannot see the drawing, so write
  it as a sentence about the system, not "diagram of the system".
- **A figure is not a substitute for the trace.** Stepping through something is
  how a reader follows it once; the diagram is what they can look back at.
  Static pictures usually beat animation, so if you can only have one, keep
  the picture.
- Two per chapter is the ceiling. A third is nearly always decoration.

## Notes that matter

**`trace` steps.** Each step is `{"at": "node", "say": "caption"}`, plus
`"from"` and `"to"` together when something should visibly move. Node names are
resolved **inside their own container**, so two traces in one course can both
call a node `client` without interfering. The attribute is single-quoted, so an
apostrophe inside a caption ends it early and the JSON will not parse — write
"the user request" rather than "the user's request".

**`annotated` code.** One `<span class="cl">` per line of source. An empty one
is a blank line. The stylesheet collapses the newlines between them, so what
you see is one rendered line per source line. Put the real file path and line
numbers in `.annotated__file` — `verify.py --src` reads it when reporting a
snippet that does not match the repository.

**`match` keys.** A slot's `data-u-slot` is the key of the chip that belongs in
it. A slot whose key matches no chip can never be answered correctly, so the
verifier treats it as an error. Placement works by dragging, by tapping a chip
and then a slot, and by keyboard.

**`check` answers.** `data-u-correct` must equal one of the `data-u-answer`
values. Results are announced to screen readers, which is why the result
element carries `aria-live`.

**`gloss`.** Definitions render in the browser's top layer, so they cannot be
clipped by anything they sit inside, and they close on `Esc` without any code.
Ids must be unique across the whole course; `scaffold.py gloss "term"` derives
one from the term.

## Colours for actors

Five are defined: `--cast-1` through `--cast-5`. Use them for avatars in a
`thread` and glyphs in a `map`, and keep a given part the same colour every
time it appears across the whole course. They adjust themselves in dark mode.

## Adding a part

Add the markup to `toolkit/snippets/`, the styles to `course.css`, and a
`part("name", …)` block to `course.js`. Then add it to `KNOWN_PARTS` in
`verify.py` and give it a case in `test/fixture.html` with assertions in
`test/harness.js` — an unwired part that silently does nothing is the failure
this project exists to prevent.
