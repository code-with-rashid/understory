# Copilot instructions — Understory courses

When asked to build a course from a codebase, follow `INSTRUCTIONS.md` at the
repository root.

- Generate chapters with `python3 scaffold.py chapter …`; never hand-write the
  markup for an interactive part.
- Replace only the `TODO` text in generated files.
- Never add inline event handlers; parts are wired by `data-u` attributes.
- Quote code verbatim from the real files, with the path and line numbers.
- Finish with `python3 build.py && python3 verify.py --src <repo>` and fix
  every ERROR it reports.
