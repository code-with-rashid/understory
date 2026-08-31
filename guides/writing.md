# Writing the content

Read this before writing your first chapter.

## Simplicity is the whole job

A course that is accurate and complete and *feels hard* has failed. Four
findings from the research on how people learn should override any instinct to
be thorough:

**Cut, don't add** (Mayer's coherence principle). People learn better when
extraneous material is removed — not when helpful extras are included. Every
component, every definition, every sentence has to earn its place by teaching
something the reader needs. An interactive part with nothing to teach makes the
course worse, not richer.

**Name things before you connect them** (Mayer's pre-training principle).
People learn a process better when they already know the names and jobs of its
parts. Never introduce a new component *and* a new interaction in the same
breath. Chapter one can be nothing but names and shape.

**Concrete first, abstraction after** (the curse of knowledge). Experts organise
knowledge by structure — layers, patterns, contexts — because that is efficient
*once you already understand it*. Beginners need a specific case first, with the
abstraction arriving afterwards to explain what they just saw. Explaining a
codebase by touring its architecture is the expert's mental model imposed on
someone who has not earned it yet.

**Follow one real task** (Carroll's minimalism). Start from something the reader
actually does with the software and follow it. Introduce each part at the moment
the story needs it, and not before. A part that never appears in the journey
probably does not belong in the course.

There is also a limit on how much can be held at once. Two or three named things
per screen is the ceiling; four or more and the reader is managing a cast list
instead of following a thread. The verifier enforces a budget — about four
interactive parts, seven new terms, two code passages, and 950 words per chapter
— and those are ceilings, not targets.

Finally: a page that *looks* dense reads as difficult before a word of it is
read. Judgements of visual complexity form in around 50 milliseconds. Fewer
objects, more space, one visual per idea.

## Depth without density

The two goals pull against each other only if depth is put on the surface. It
does not have to be.

A `depth` block shows a single line and folds the mechanism behind *How it
actually works* and *Where it gets subtle*. A reader skimming gets a clean page;
a reader who wants the machinery opens it. The verifier counts **visible** words
against the budget, not total words, so folding lets a chapter be twice as deep
at the same apparent weight.

What goes in each layer:

| Layer | Holds |
|---|---|
| The line | What is true, stated so it can be repeated to someone else |
| How it actually works | The steps, in order, including the awkward one |
| Where it gets subtle | The edge case, the ordering constraint, the thing that surprises maintainers |

## Writing something defensible

A `defend` block puts a hard question to the reader and makes them try before
it answers. Two rules make it work.

**The question has to be fair and hard.** "Why is this good?" teaches nothing.
The right question is the one a sceptical senior engineer actually asks: *why
not the simpler thing, why not the standard thing, isn't this over-engineered,
what happens under load, isn't the boundary already elsewhere.* If you cannot
imagine someone respected asking it, it is not worth including.

**Include the answer that fails.** Naming the plausible-but-weak answer, and
the single follow-up that dismantles it, is most of the value. It is the
difference between a reader who repeats a slogan and one who knows where the
slogan runs out.

A `tradeoff` card holds a decision: what was chosen, what was rejected, what it
cost, and what would make you revisit it. Every field must come from the
repository — a decision record, a commit message, a design note. The cost field
is not optional and is never "none": a decision with no cost was not a decision.

## The reader

They have used the software. They have never read it. They are not stupid and
they are not a beginner at their own job — they are a beginner at this one.
Write the way you would explain your work to a sharp colleague from another
department: no jargon without a definition, no ceremony, no flattery.

Two failure modes, equally bad. Writing down to them produces cheerful mush
that teaches nothing. Writing past them produces a reference manual they close
after two screens.

## Prefer interactions that make the reader produce something

The evidence ranks engagement modes: interactive beats constructive beats
active beats passive, with measurable gains at each step. Clicking "next" on an
animation is *active* — better than reading, weaker than it looks. The parts
that make the reader **generate** — write a prediction before checking
(`fieldwork`), attempt an answer before the reveal (`defend`), recall from
memory (`recall`) — are worth more per minute than any amount of clicking.
When choosing between two parts for the same content, choose the one that makes
the reader produce something before it shows them anything.

## Three sentences, then show something

The hard rule: **no more than three sentences before a visual.** If a fourth
wants to exist, it is a sign that the idea has a shape, and shapes belong in
cards, steps, a trace, or a diagram.

| If you are writing | Use instead |
|---|---|
| a list of three or more things | `cards` or `rows` |
| a sequence of events | `steps`, or `trace` if it moves between parts |
| "A calls B, which calls C" | `trace` or `thread` |
| what a piece of code does | `annotated` — never a paragraph about code |
| "this file does X, that one Y" | `tree` |
| a comparison of two approaches | `stack` |
| "A calls B, then B calls C, and D waits" | a `sequence` figure |
| "this may depend on that, but not the reverse" | a `layers` figure |
| "it can be in one of these states" | a `states` figure |
| any number worth comparing with another number | a `bars` figure |

A diagram earns its place when the thing being explained has a *shape* —
an order, a direction, a boundary, a size. Prose is bad at all four and a
picture is good at all four. Prose is better than a picture at *why*, so the
two belong together: the figure carries the shape, the paragraph beside it
carries the reason.

The verifier warns when a chapter's paragraph-to-visual ratio drifts past four
to one. That warning is usually right.

## Explaining code

Show the real thing. Copy the passage out of the file, unmodified, including
its indentation and its awkward bits. A reader who opens the repository and
finds something different from what they were taught stops trusting the course.

If a passage is too long, do not trim it — pick a different passage. Every
codebase has short, self-contained moments; find one.

The plain-English column explains *why*, not *what*. "Set the Authorization
header" is a translation nobody needed. "Prove who we are, or the server hangs
up on us" is the one worth reading. One note per line or two of code, in the
order the code runs.

## Metaphors

Every chapter gets exactly one, and it must be a metaphor that could not have
been used for the previous chapter. The test: if the metaphor would fit three
different concepts equally well, it is decoration, not explanation.

Never reach for the restaurant, the kitchen, the recipe, or the chef. They are
the first thing everyone reaches for and they explain almost nothing. Better
ones are specific: a topological sort is a build order, a cache is a
photocopier, a retry with backoff is knocking louder and then walking away,
message passing is the postal service, backpropagation is an incident review.
Introduce the metaphor, then immediately land it: "in this code, that is…".

## Inline definitions

Define a word the first time it appears in each chapter, whenever there is any
chance the reader does not have it. Err heavily toward too many: function,
class, module, flag, endpoint, dependency, thread, buffer, schema, and the
names of tools they may never have heard of.

A definition is one or two sentences of ordinary language, and it ends by
handing the term back as something the reader can *use*:

> A **flag** is an option you add to a command to change how it behaves, like
> adding `--json` to get structured output instead of plain text. You would say
> to an assistant: "add a flag for verbose output."

Skip the ones they already own. Somebody working in marketing analytics does
not need "conversion rate" defined.

## Refuting a misconception

A `myth` block names a wrong belief once — struck through — and then makes the
correction more vivid than the myth. The evidence for refutation over plain
exposition is strong (76 studies), with one sharp caveat that is a rule here:
**only refute assumptions readers genuinely arrive with.** Refuting a rare
misconception teaches it — repetition breeds familiarity, and familiarity reads
as truth. One per chapter at most, and the correction must carry more weight,
more specificity and more memorability than the myth it replaces.

The test for whether a myth qualifies: would a smart newcomer, asked to guess,
produce it unprompted? "Logged in means isolated" passes. An obscure confusion
about one library's flag does not.

## Fieldwork

A `fieldwork` block is the bridge between course-knowledge and
codebase-knowledge, and it is where transfer actually happens. Three rules:

- **Read-only and verifiable.** "Open this file" and "run ls on this folder"
  always work; "run the app" depends on setup the reader may not have. Every
  prediction must have a definite answer the file itself settles.
- **Predict before looking.** The instruction must make the reader commit —
  "write down what you expect" — because an unsuccessful retrieval attempt
  still strengthens the memory, and a prediction-free look strengthens nothing.
- **The best fieldwork targets an edge.** Not "find the middleware" but "what
  happens when the same header arrives twice?" — a case the chapter did not
  cover, answerable from what it taught.

## Recall

The `recall` section is the last thing in the course, and it is retrieval, not
recognition: open prompts ("explain to a colleague why…"), never multiple
choice — recognising a right answer is a much weaker act than generating one.
One prompt per chapter plus one spanning the whole journey is the floor. The
folded answer lists what a complete response *names*, so readers can grade
themselves. And say plainly when to return: in three days, then next week.
That instruction is the single highest-leverage sentence in the course.

## Questions

One check per chapter, at the end, two or three questions. They exist to make
the reader think for fifteen seconds, not to score them.

Ask what they would *do*:

- "You want to add X. Which part would you change, and why that one?"
- "A user reports Y is broken. Where do you look first?"
- "An assistant suggests Z. What would that cost you later?"
- "Follow what happens when someone does W."

Never ask what something stands for, which file holds a thing, or anything
answerable by scrolling up. Definitions are what the inline definitions are
for.

Both explanations teach. The one for a wrong answer says what to reconsider
and why, without saying "wrong". The one for a right answer states the
principle that made it right, so the reader can carry it somewhere else. And
vary which option is correct — the verifier warns when every answer is the
same letter.

## Tone

Plain, warm, unhurried, specific. Contractions are fine. Jokes are fine when
they arrive on their own; a joke you had to reach for reads as filler. Give the
parts of the system personalities and let them talk to each other in the
`thread` — it is the single most-read part of any course, because it turns
architecture into gossip.
