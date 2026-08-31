---
name: understory
description: "Turn a codebase into an interactive single-page HTML course that teaches a non-programmer how the code actually works — scroll-based chapters, real code beside plain-English readings, step-through data-flow animations, component dialogues, and questions that test judgement rather than recall. Use when someone asks to turn a repository or project into a course, tutorial, walkthrough, or interactive explainer; when they say 'teach me this codebase', 'explain how this project works', 'make a course from this repo', 'onboarding material for this service', or point at a GitHub URL and ask what it does under the hood. Produces a self-contained directory that opens in a browser with no build step and no network."
license: MIT
compatibility: Requires Python 3.9+ and a POSIX shell or equivalent; the optional engine test suite uses a local Chrome or Chromium.
metadata:
  version: "1.2"
  author: rashidmahmood
---

# Understory

Follow `INSTRUCTIONS.md` in this skill directory from start to finish. It is
harness-neutral and complete; this file only tells you how to begin.

## Begin

If the user named a GitHub URL, clone it somewhere scratch first. If they said
"this project", use the working directory. If they have not said which codebase,
introduce yourself and ask for one:

> I can turn a codebase into an interactive course that teaches how it works —
> no programming background needed. Point me at a local folder, a GitHub link,
> or say "this one" if we are already in it. I will read the code, work out how
> the pieces fit, and build you a browser page with animated walkthroughs,
> plain-English readings of real code, and questions to check it landed.

Then read `INSTRUCTIONS.md` and work through its four phases: read the
codebase, plan four to six chapters, scaffold and fill one chapter at a time,
then build and verify.

## The parts of this skill

| File | Read it when |
|---|---|
| `INSTRUCTIONS.md` | first, always — the whole procedure |
| `guides/writing.md` | before writing the first chapter |
| `guides/components.md` | when you need a part you have not used before |
| `guides/pitfalls.md` | before declaring the course finished |
| `toolkit/` | never read it; run it |

## When not to use this

Not for API reference documentation, user manuals, or changelogs — those are
different documents with different shapes. Not for explaining a single function
or file (answer directly instead). And not worth running on a repository the
user only wants summarised; a course is for someone who needs to *keep* the
understanding.

## The two things that matter most

**Scaffold, then fill.** `python3 scaffold.py chapter …` emits markup already
wired to the engine. Replace the `TODO` text and nothing else. Hand-writing an
interactive part is how courses end up with controls that quietly do nothing.

**Verify before you show anyone.** `python3 build.py && python3 verify.py --src <repo>`
must exit clean. Every failure it catches is invisible in a browser, which is
exactly why it exists.
