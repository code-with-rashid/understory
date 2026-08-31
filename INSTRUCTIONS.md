# Understory — build an interactive course from a codebase

You are turning a codebase into a single-page HTML course that teaches a
non-programmer how that code works. This file is the whole procedure. It
assumes nothing about your harness beyond a shell, a filesystem, and Python 3.

## What you are making

A directory that opens in any browser with no build step and no network:

```
my-course/
  index.html      ← generated; never edit by hand
  course.json     ← title, palette, path to the codebase
  chapters/       ← one HTML file per chapter; the only files you write
  course.css      course.js      shell.html
  build.py        verify.py      scaffold.py      snippets/
```

Four to six chapters. Each one teaches a single idea, shows real code beside a
plain-English reading of it, and ends with a question the reader has to think
about rather than remember.

## What "understood it" has to mean

Not "could summarise it". The bar is that the reader can **explain the mechanism
step by step, and defend the design against someone who knows the field.**

Those are different skills and a course can accidentally deliver neither.
People reliably feel they understand a system until they are asked to explain
how it actually works, at which point the feeling collapses — the illusion of
explanatory depth. A course made of clear summaries *manufactures* that illusion.
It reads beautifully and leaves nothing behind.

Three things close the gap, and they shape everything below:

- **Mechanism, not just outcome.** What each step does, in order, including the
  part that is fiddly. A reader who only has the outcome cannot answer a
  question they have not already been asked.
- **The rejected alternative.** A decision is only understood next to the option
  it beat and the price it paid. This is what turns knowledge into a position
  you can hold.
- **Being challenged before being told.** Trying to answer and failing is what
  makes the answer stick. Every chapter puts a hard question to the reader
  before it hands one over.

## A course is one pass. Understanding is a schedule.

Even a perfect single read-through cannot produce deep understanding of a large
system, and pretending otherwise is how a reader finishes a good course feeling
worse — they now see how much they do not know, with no shape to it. Three
findings from the learning literature dictate the output's shape:

- **One exposure decays.** Across 242 studies, the two most effective techniques
  known are distributed practice and retrieval practice — returning to material
  over days, and pulling it from memory rather than re-reading it. So every
  course **ends with a `recall` section**: free-recall prompts with folded
  answers, written to be re-taken after three days and again after a week.
- **Reading is not contact.** Knowledge transfers when it is used in the place
  it applies. So every course includes **`fieldwork`**: at least two exercises
  that send the reader into the actual repository — open this file, write down
  what you predict for this case, then check. Predict-first is non-negotiable;
  checking without a written prediction is just more reading.
- **The unknown must be bounded.** A reader cannot plan learning against
  unknown-unknowns. So chapter one carries a **`territory`** map: every area of
  the system named with its one-line job and size, the areas this course covers
  marked, and the rest routed — to a named next course, or explicitly deferred.
  Finishing should feel like "I know exactly what I have not done yet", never
  "there is an unbounded amount I do not understand".

This also changes what the skill produces: **a course is one pass through one
journey, and the product is a series.** Record the series in `course.json`
(`"series": [{"title": ..., "covers": [...]}, ...]`) and make the territory map
agree with it. When the user asks for more, generate course two against the
same map — do not stretch course one.

## Who it is for

Someone who directs AI coding tools in natural language and has never been
taught computer science. They may have built this software themselves without
reading it, or found it and want to know how it works.

Assume no technical vocabulary at all. Not "function", not "API", not "flag".
Anything that would not come up over dinner gets an inline definition the first
time it appears in a chapter.

Their goal is not to become an engineer. It is to steer AI better, to notice
when it is wrong, to get unstuck without waiting for someone else, and to
describe what they want precisely enough to get it. Every chapter should leave
them able to do one of those things they could not do before. If a chapter
does not, cut it.

## The procedure

### 1 — Read the codebase

Before writing anything, find out what the software actually does and how. Read
the README, the entry point, and whatever the entry point reaches. Look for:

- the handful of parts that matter, and what each is responsible for
- the path one real user action takes, end to end
- where data crosses a boundary — network, disk, database, another process
- the decisions someone clearly made on purpose, and what they bought
- the failure that would be hardest to debug from the outside

Work out what the software is for by yourself. Do not ask the user to explain
their own project; they may know it only from the outside, which is why they
want the course.

Note the exact file paths and line numbers of five to ten short passages worth
teaching. Five to ten lines each, and choose passages that are *already* short
rather than shortening one yourself.

**Also give every abstract concept one example and one near-miss.** The
research on unambiguous teaching is blunt: a concept is fixed by juxtaposing an
example with a non-example that differs only in the critical feature. "A port
describes the job" teaches less than "this is a port; this same file with a
vendor's cursor type in it is no longer a port, and here is why". The
`defend` part's "what will not survive" line is this rule applied to arguments;
apply it to concepts too.

**Then go and find the reasoning.** This is the step that separates a course
someone can defend from a course they can only recite, and it is the one most
easily skipped, because the reasoning is never in the code:

- `docs/adr/`, `docs/decisions/`, `*.adr.md` — architecture decision records are
  the jackpot. They state the context, the option chosen, the options rejected
  and the consequences, in the authors' own words.
- `docs/architecture/`, design notes, RFCs, the wiki the README links to.
- `git log` on the file that surprised you. Commit messages and merge requests
  often carry the argument.
- Long comments that explain *why* rather than what, and tests named after the
  bug they prevent.

Collect at least three real decisions with their costs. **Never invent a
rationale.** An invented "why" is worse than no "why": it is the thing that
collapses when someone who was in the room asks a follow-up.

### 2 — Plan the chapters

**Pick one journey and follow it.** Not a tour of the architecture — one real
thing a person does with the software, followed from the moment they do it to
the moment they see a result. Everything the reader meets, they meet because
the journey reached it.

This matters most on a large codebase. A system with a dozen modules has a
dozen boxes an expert can draw, and drawing them is the fastest way to lose a
beginner: it is the expert's own mental model, which they earned by working in
it for months. Following a single request through four of those modules teaches
more than naming all twelve.

| Chapter | Does this |
|---|---|
| 1 | What the software is for, and the shape of the journey — names only, no mechanism |
| 2 | The journey starts: what happens the moment the request lands |
| 3 | The one idea that explains why the code is laid out the way it is |
| 4 | The part that is genuinely hard, done properly |
| 5 | How it fails, and how you would know |

Chapter four matters more than it looks. Every serious system has one place
where the problem is actually difficult — untrusted input, concurrency, money,
partial failure. That is where the real engineering is, it is what an expert
will ask about first, and skipping it is what makes a course feel like a
brochure.

Four chapters is a good default, five if the journey genuinely needs it, six at
the very most. Fewer thick chapters always beat more thin ones, and a chapter
that does not leave the reader able to do something new should be cut rather
than padded.

**What to leave out.** Everything the journey does not touch. A module the
request never reaches, a pattern used once, the build system, the test setup,
the folder you found interesting — leaving these out is not a compromise, it is
the design. Anything omitted is still in the repository if the reader ever
needs it.

**Order chapters by dependency.** Nothing may be used before it is introduced:
if chapter two's explanation quietly leans on an idea chapter four teaches, the
order is wrong, not the explanation. The territory map is the check — walk it
and confirm each chapter needs only what came before.

Do not present the plan for approval. Build it. Corrections are cheaper to make
against something real.

### 3 — Write the chapters

Scaffold each chapter first, then fill it in. The scaffolder emits markup that
is already wired to the engine, so you write prose and never wiring:

```bash
# once, from wherever this project lives — copies the toolkit into the course
python3 <path-to-understory>/toolkit/scaffold.py init "How X Works" \
        --palette pine --source ../x --root ./x-course

# from inside the course directory, from then on
cd x-course
python3 scaffold.py chapter 1 what-it-does --title "What it does" \
        --parts beat,rows,annotated,trace,check
python3 scaffold.py parts                # list the available parts
python3 scaffold.py gloss "idempotent"   # print a wired inline definition
python3 scaffold.py figure sequence request-lifecycle   # start a diagram
```

Diagrams live in `diagrams/*.json` and are rendered to inline SVG by the build,
so they work offline and in print. Reach for one whenever the thing you are
explaining has a shape: an order (`sequence`), a direction (`layers`), a set of
connections (`flow`), a set of states (`states`), or a size worth comparing
(`bars`). If the repository already has diagrams — Mermaid in the docs, an
architecture page — read them first: they tell you how the team pictures their
own system.

Palettes: `pine`, `clay`, `indigo`, `moss`, `plum`, `slate`. Each has a
light and a dark variant, both checked for contrast; pick by mood.

Then replace every `TODO` in the generated file with real content, and nothing
else. `verify.py` fails while any `TODO` remains.

Write one chapter at a time, all the way through, before starting the next.
Chapters written in a batch get thinner as the batch goes on.

Read `guides/writing.md` before the first chapter and `guides/components.md`
when you need a part you have not used yet.

### 4 — Build, verify, test, look

```bash
python3 build.py                # chapters/*.html + course.json → index.html
python3 verify.py --src ../x    # must exit clean
```

`verify.py` catches what a browser will not tell you: unfilled scaffolding,
duplicate ids, a step that names a node which does not exist, malformed JSON in
an attribute, a quiz whose correct answer matches no option, a chapter with no
definitions, code that does not match the real source file **to the byte and to
the line number**, fieldwork paths that do not exist, and coverage the
territory claims but the chapters never visibly keep. Fix every ERROR and run
it again. Treat WARN as a to-do list.

The build also stamps a colophon on the page — which repository and commit the
course describes, and when it was generated — so a stale course announces its
own staleness instead of quietly rotting.

Then open `index.html` and use it. Click every control. Open the browser
console — anything prefixed `[understory]` is a component telling you it was
wired wrongly.

**Hand it over properly.** The course directory needs its sibling files, so
never send someone `index.html` on its own — the page arrives unstyled and
inert. Either give them the whole folder, or build the single-file version:

```bash
python3 build.py --inline --out "How X Works.html"
```

That folds the stylesheet and the engine into the page. One file, no network,
no server: it can be emailed, dropped in a chat, or opened from a USB stick.
Tell the user where it is and how to open it — `open "How X Works.html"` on a
Mac, `xdg-open` on Linux, `start` on Windows.

## Rules the verifier enforces

- Every chapter: one check, one inline definition, one interactive part, and
  **one `defend`** — an objection the reader must try to answer before the
  answer is revealed.
- **At least three `tradeoff` cards** across the course, each citing where the
  rationale is recorded. A card with no source is a rationale you invented.
- A `depth` block wherever there is mechanism worth folding away.
- Every course: at least two code passages — but *not* one per chapter. A
  chapter that is purely orientation is doing its job.
- A complexity budget per chapter, enforced as warnings: about four interactive
  parts, seven new terms, two code passages, 950 words. These are ceilings.
  Coming in well under them is a good sign, not a gap to fill.
- Code shown must appear **verbatim** in the source repository. Choose short
  passages instead of trimming long ones. `--src` checks this.
- No inline `onclick` anywhere. Every part is wired by its `data-u` attributes;
  if you find yourself writing a handler name, you are copying markup from the
  wrong place.
- Every `id` unique across the whole assembled page.
- No apostrophes inside `data-u-steps`, which is a single-quoted attribute.
  Write "the user request", or `&apos;`.

## If your harness can run work in parallel

Optional, and only worth it above about five chapters. Write a one-page brief
per chapter first — metaphor, the passages already pasted in with their file
paths, which parts to use, what the chapters either side cover — then hand one
brief per worker. A worker needs its brief and `guides/writing.md`, and nothing
else: not the codebase, not this file, not the other briefs.

Without parallel workers, do the same thing sequentially. The output is the
same; only the wall clock differs.

## What good looks like

The reader scrolls through without hitting a wall of text, stops at each check
long enough to actually think, and comes away able to open the real repository
and recognise what they are looking at.
