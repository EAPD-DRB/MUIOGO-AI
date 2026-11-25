# Skills catalogue

Skills are instruction packs that teach an AI assistant how to do a specific
modelling job properly — the methods, the checks, and the traps. They are plain
folders of Markdown (plus a few helper scripts) following the
[Agent Skills](https://agentskills.io) open standard, so they work with any
assistant that supports it; nothing here is tied to one product.

## Nothing to install (in this repository)

Open this repository in Claude Code or Codex and the skills are already
active. The files live in `.agents/skills/`, the cross-assistant standard
location that Codex reads from a repository, and `.claude/skills/` holds an
identical copy of each, which is how Claude Code reads them.

## How you use one

Describe the job in plain language and your assistant picks the matching skill:

> assess how well this CLEWs model is calibrated

To name one explicitly, use `/skill-name` in Claude Code or `$skill-name` in
Codex.

**[docs/USING_THE_SKILLS.md](docs/USING_THE_SKILLS.md) has three worked
examples** — asking questions about a run you already have, reviewing a model's
structure, and running a scenario — with the exact prompts and the real numbers
to expect from the demo model.

## To use them everywhere else

To get the skills in your own model repositories, or in every project you open:

```bash
./scripts/install-skills.sh
```

It asks which assistant you use (Claude Code, Codex, both, or a folder you
name) and copies the skills there. Re-run it any time to update. By hand, copy
any folder from `.agents/skills/` into your assistant's skills directory
(`~/.claude/skills/` or `~/.codex/skills/`) and restart the assistant.

## Start here

| Skill | What it does |
|---|---|
| `muiogo-workspace` | Finds your installation, lists what is available, and routes the request to the right model family and skill. Every other skill assumes this one has run. |

## Getting models in and out

| Skill | What it does |
|---|---|
| `muiogo-provision` | Installs an OG country model, imports a case archive or Excel workbook, exports a shareable zip, and validates inputs before a long solve. |
| `pull-handoff` | Clones or fast-forwards the CLEWs country repos, unzips their current MUIO cases into repository-local working trees, and maintains the MUIOGO DataStorage symlinks. |
| `push-handoff` | Zips the repository-local cases without solver results, checks their symlinks and SHA-256, then commits and pushes the intended country-repo changes. |

## MUIOGO — running models and analysing results

| Skill | What it does |
|---|---|
| `muiogo-run` | Starts the server, solves a case or a batch, diagnoses failed solves, and collects results. |
| `muiogo-scenarios` | Builds policy scenarios (a carbon tax, a renewable target, a demand change), combines them into runs, and sweeps matrices. |
| `muiogo-analyze` | Compares runs, checks whether a solve is trustworthy, charts trajectories, and writes short policy notes. |

## CLEWs — energy, land, and water models

| Skill | What it does |
|---|---|
| `build-clews-model` | Builds a whole-country CLEWs model from scratch with the upstream CLEWs Global workflow, then imports it into MUIO as a solved, portable case. |
| `assess-clews-calibration` | Judges how well a model is calibrated to its country, grades it, and says what to fix first. |
| `calibrate-clews-model` | Implements the calibration: stocks, lifetimes, demand, costs, efficiencies, and historical pins, changed equation-first and against sources. |
| `clews-model-review` | Checks a model's structure and data consistency against a reference model — orphaned IDs, unit slips, missing sectors. |
| `clews-model-fix` | Makes structural repairs that cannot move a solved number — unreferenced objects, placeholder descriptions, technology groups. |
| `add-fisheries-sector` | Adds a complete, source-traceable fisheries sector to a solved model without distorting existing results. |
| `add-environmental-accounting` | Adds water and land environmental accounting to a CLEWS model and quantifies what changed. |

## Understanding the models

| Skill | What it does |
|---|---|
| `muiogo-explain` | Explains what a model contains, how it is calibrated, the theory behind it, and the intuition for its results — grounded in the model's own files, not from memory. |

## Coupled OG-CLEWS

| Skill | What it does |
|---|---|
| `og-clews-linked-run` | Runs coupled analyses through ogclews-link: an energy or climate policy's effect on the economy, through a named transmission channel. |

## OG — macroeconomic country models

| Skill | What it does |
|---|---|
| `og-run` | Installs and runs a model the way its users do, checks the environment before a run (the preflight), monitors it, and collects the output. |
| `og-country-calibration` | The calibration playbook: lessons on each block with the check that proves it, the history behind them, and tracing where an existing value came from. |
| `og-multi-industry-calibration` | Builds or reviews a multi-industry calibration from a SAM or input-output tables, consistent with the single-industry model. |
| `og-scenario-report` | Designs reforms and turns finished runs into results: the standard deliverable and bespoke analysis, charts and write-ups. |

## Running models safely

| Skill | What it does |
|---|---|
| `og-solver-diagnosis` | A root-cause protocol for solves that fail to converge, oscillate, or produce nonsense. |

The go/no-go check before a long run is part of `og-run`.

## Notes for maintainers

Each skill is one directory under `.agents/skills/` containing `SKILL.md` (the
instructions, with a name and description in the frontmatter), optional
`references/` for deeper material, `scripts/` for helpers, and `assets/` for
templates. Some also carry `agents/openai.yaml` with Codex display metadata.

`.agents/skills/` is the source here, and `.claude/skills/` holds identical
copies (copies, not symlinks, so a Windows clone keeps working). After adding,
renaming or editing a skill, refresh and check them:

```bash
./scripts/install-skills.sh --sync
./scripts/install-skills.sh --check
```

**Where each skill is edited.** Every skill has one home:

- **[Model-tools](https://github.com/EAPD-DRB/Model-tools)** holds the OG skills
  (`og-run`, `og-solver-diagnosis`, `og-country-calibration`,
  `og-multi-industry-calibration`, `og-scenario-report`, `og-clews-linked-run`).
  They are vendored here unchanged at the commit in `scripts/MODEL_TOOLS_PIN`;
  never edit them here. Fix them in Model-tools, then move the pin:

  ```bash
  python scripts/model_tools_skills.py --update <commit>
  ./scripts/install-skills.sh --sync
  python scripts/model_tools_skills.py --check
  ```

  Model-tools is also the home of the CLEWs skills and the handoff skills; the
  copies here have drifted from it in both directions and will join the pin once
  they are reconciled.
- **This repository** holds the `muiogo-*` skills, which drive this repo's
  `muiogo` command line, and `WORLD_DISCIPLINE.md`.

Skills that no longer ship (`og-run-preflight`, `calibration-provenance`,
`og-repo-fleet-sync`, `og-analysis-studio`) are listed in
`scripts/RETIRED_SKILLS`; the installer moves any it finds in a target folder
aside.

**Approval gates** bind every skill in this repository; they are in `AGENTS.md`, which both
Claude Code and Codex read at the start of every session here.

The planned `muiogo-interpret`, `muiogo-visualize`, and `muiogo-brief` ship
together as `muiogo-analyze`; the planned tutors ship as `muiogo-explain`.
See [docs/SCOPE.md](docs/SCOPE.md).

Skills here talk to MUIOGO over its HTTP API only — through the `muiogo`
command line — never by importing its backend code. Each model family runs from
its own environment: MUIOGO from its own venv, each OG country model from its
own, and the link from its own (it never imports `ogcore`; it subprocesses the
model's own interpreter).
