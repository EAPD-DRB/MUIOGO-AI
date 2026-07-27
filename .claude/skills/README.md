# Skills

One directory per skill, `<name>/SKILL.md` plus any reference files. Names and
scope come from the inventory in `docs/SCOPE.md`:

- Group A (operate): `muiogo-install`, `muiogo-run`, `muiogo-scenarios`
- Group B (OG integration): `og-clews-linked-run`
- Group C (analyze): `muiogo-interpret`, `muiogo-visualize`, `muiogo-brief`
- Group D (teach): `muiogo-tutor`, `og-clews-tutor`

Ground rules: skills carry workflow and judgment; anything mechanical
(HTTP calls, session handling, polling, file paths) belongs in
`client/` so skills stay short. Skills talk to MUIOGO through the client or
its HTTP API only — never by importing MUIOGO code.

## Imported: the OG skill family (2026-07-27, from Model-tools `og-skills`)

The full practitioner set for OG-Core work, installed project-scoped here. This repo is the
**canonical home** for the five infrastructure skills; the three general-audience ones are
mirrored from Model-tools (canonical there — update there first, re-copy here):

| Skill | Canonical | What it does |
|---|---|---|
| `og-country-calibration` | Model-tools | Calibration playbook: methods, pitfalls, house rules |
| `og-scenario-report` | Model-tools | OUTPUT dirs → standard charts + tables + narrative (`scripts/scenario_report.py`) |
| `og-analysis-studio` | Model-tools | Scenario design, free-form exploration, bespoke code-generated visuals & write-ups |
| `og-run-preflight` | **here** | GO/NO-GO before any run: branch+HEAD, 3 import-shadowing vectors, venvs (`scripts/preflight.py`) |
| `og-solver-diagnosis` | **here** | Root-cause protocol for sick SS/TPI solves + real failure taxonomy |
| `og-repo-fleet-sync` | **here** | One change → N country repos, tracked; never pushes/PRs unasked |
| `worktree-orchard` | **here** | Read-only checkout/worktree sprawl inventory (`scripts/orchard.py`) |
| `calibration-provenance` | **here** | Trace any parameter to its authoritative source; record the chain |

Overlap note: parts of planned `muiogo-visualize`/`muiogo-brief` overlap
`og-analysis-studio` — reconcile before building those.

### Approval gates (binding on every OG skill above)

Skills **propose, draft, and prepare; the user decides**. A skill may edit files, commit locally,
and produce drafts — and must stop and ask before: **pushing** to any remote, **creating a PR**,
or **merging** anything (merges are always the user's); **launching long computations** (a TPI
solve, a battery, anything beyond a couple of minutes — propose the command and duration, the
user launches; a passing preflight is a precondition, never an authorization); **fleet-scale
actions** (never "one approval, N repos"); **destructive cleanup** (emitted only as commands for
the user to run). If a skill's text ever seems to conflict with this section, this section wins.
