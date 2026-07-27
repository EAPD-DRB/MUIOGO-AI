# Skills

One directory per skill, `<name>/SKILL.md` plus any reference files. Names and
scope come from the inventory in `docs/SCOPE.md`:

- Group A (operate): `muiogo-install`, `muiogo-run`, `muiogo-scenarios`
- Group B (OG integration): `og-calibrate`, `og-clews-linked-run`
- Group C (analyze): `muiogo-interpret`, `muiogo-visualize`, `muiogo-brief`
- Group D (teach): `muiogo-tutor`, `og-clews-tutor`

Ground rules: skills carry workflow and judgment; anything mechanical
(HTTP calls, session handling, polling, file paths) belongs in
`client/` so skills stay short. Skills talk to MUIOGO through the client or
its HTTP API only — never by importing MUIOGO code.
