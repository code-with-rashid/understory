# Understory

> This file follows the AGENTS.md convention. If your tool supports the Agent
> Skills standard (SKILL.md), prefer `python3 install.py` — the skill directory
> carries the same instructions with progressive loading.

To turn a codebase into an interactive HTML course, follow `INSTRUCTIONS.md` in
this repository, start to finish.

Short version:

```bash
python3 toolkit/scaffold.py init "How X Works" --palette pine --source ../x
python3 scaffold.py chapter 1 <slug> --title "..." --parts beat,annotated,check
# replace every TODO with real content, one chapter at a time
python3 build.py && python3 verify.py --src ../x
```

Non-negotiable:

- Never hand-write wiring. Scaffold the chapter, then fill in the `TODO`s.
- Never write an inline `onclick`. Every part is bound by its `data-u`
  attributes.
- Code shown to the reader must appear verbatim in the source repository.
- `verify.py` must exit clean before the course is finished.
- No apostrophes inside `data-u-steps` — it is a single-quoted attribute.

`guides/writing.md` has the content rules. `guides/components.md` has the parts.
