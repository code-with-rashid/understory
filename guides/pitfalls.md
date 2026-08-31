# What goes wrong

Everything here is silent in a browser: no error, no visual clue, just a thing
that quietly does nothing. `verify.py` and `test/run.py` catch most of it.
Run both.

### Scaffolding left half-filled
`TODO` text shipped into the course. It looks like content at a glance,
especially in a component you did not open. The verifier fails on any `TODO`.

### Code that does not match the source
Trimming a passage to fit, re-indenting it, renaming a variable for clarity.
The reader opens the real file, sees something else, and stops believing the
rest of the course. Pick a shorter passage instead. `verify.py --src` compares
every snippet against the repository.

### An apostrophe in a trace caption
`data-u-steps` is a single-quoted attribute, so `"the user's request"` ends it
early and the JSON never parses. That trace goes dead while everything around
it keeps working. The verifier parses the JSON; the engine also warns in the
console.

### Reused ids
Two components with the same id anywhere in the assembled page. Whatever looks
one up finds the first, which may be four chapters away. Trace nodes are named
with `data-u-node` and resolved within their own container precisely so this
cannot bite, but ids you add yourself still can.

### One chapter, one metaphor
Reaching for the same image twice — and especially reaching for the restaurant
— stops the metaphor doing any work. The verifier warns on the usual suspects,
but it cannot see the ones you invented.

### A chapter that is all prose
Three sentences, then a visual. A chapter that reads like a textbook has failed
even if every sentence in it is true. The verifier warns past four paragraphs
per visual block.

### Definitions only in the first chapter
Define a term on first use *in each chapter*. People do not read straight
through, and a reader who lands in chapter four should not be stranded.

### A quiz that tests recall
"What does API stand for?" tests whether they scrolled up. Ask what they would
change, where they would look, or what a suggestion would cost them.

### Every correct answer in the same position
Easy to do when you write the right answer first each time. Readers notice
before you do. The verifier warns when four or more questions share a letter.

### Assuming a wide screen
A row of three buttons plus a label is wider than a phone. Everything shipped
here wraps; anything you add must too, or the whole page scrolls sideways on
every chapter. `test/run.py` measures this at a real 375px viewport.

### Assuming JavaScript
Content is revealed on scroll, so a script that throws early would leave a
blank page. The engine isolates each component and the shell carries a
`<noscript>` fallback. Do not add a `<script>` of your own.
