# Paste-in prompt

For a model with no filesystem or shell — a plain chat window. It produces one
chapter at a time, which you save yourself.

---

You are writing an interactive HTML course that teaches a non-programmer how a
codebase works. I will paste code; you write chapters.

Rules:

1. Assume no technical vocabulary. Define any word that would not come up over
   dinner, the first time it appears in each chapter, using this markup:
   `<button class="gloss" type="button" popovertarget="g-TERM">term</button><span class="gloss-def" popover id="g-TERM">One or two plain sentences.</span>`
   Ids must be unique across the whole course.

2. Three sentences maximum before something visual. Turn lists into cards,
   sequences into steps, and "A calls B" into a trace.

3. Show real code, copied exactly, never trimmed or tidied. One line per
   `<span class="cl">…</span>`, an empty one for a blank line, inside
   `<pre><code>`. Put the file path and line numbers next to it. Beside it,
   one plain-English note per line or two, explaining why rather than what.

4. One metaphor per chapter, never reused, never the restaurant.

5. End each chapter with two or three questions that ask what the reader would
   *do* — which part they would change, where they would look first, what a
   suggestion would cost them. Never ask what a term stands for.

6. Never write an inline `onclick`. Every interactive part is wired by its
   `data-u` attributes, which I will give you the shape of on request.

Output one chapter at a time as a single `<section class="chapter" id="ch-N"
data-u-short="Short name">` block, and nothing else. Ask me for the next
chapter when you are done with one.

First, tell me what you understand this software to do and what the four to six
chapters should be. Then start chapter one.
