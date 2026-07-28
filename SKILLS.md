# Skills catalogue

Skills are instruction packs that teach an AI assistant how to do a specific
modelling job properly — the methods, the checks, and the traps. They are plain
folders of Markdown (plus a few helper scripts) following the
[Agent Skills](https://agentskills.io) open standard, so they work with any
assistant that supports it; nothing here is tied to one product.

## Nothing to install (in this repository)

Open this repository in Claude Code or Codex and the skills are already
active. The files live in `.agents/skills/`, the cross-assistant standard
location that Codex reads from a repository, and `.claude/skills/` holds one
symlink per skill, which is how Claude Code reads them. Just ask for the job in
plain language — *"assess this model's calibration"*, *"check things before I
launch this run"* — and your assistant follows the skill.

## To use them everywhere else

To get the skills in your own model repositories, or in every project you open:

```bash
./scripts/install-skills.sh
```

It asks which assistant you use (Claude Code, Codex, both, or a folder you
name) and copies the skills there. Re-run it any time to update. By hand, copy
any folder from `.agents/skills/` into your assistant's skills directory
(`~/.claude/skills/` or `~/.codex/skills/`) and restart the assistant.

## CLEWs — energy, land, and water models

| Skill | What it does |
|---|---|
| `build-clews-model` | Builds a whole-country CLEWs model from scratch with the upstream CLEWs Global workflow, then imports it into MUIO as a solved, portable case. |
| `assess-clews-calibration` | Judges how well a model is calibrated to its country, grades it, and says what to fix first. |
| `clews-model-review` | Checks a model's structure and data consistency against a reference model — orphaned IDs, unit slips, missing sectors. |
| `add-fisheries-sector` | Adds a complete, source-traceable fisheries sector to a solved model without distorting existing results. |
| `add-environmental-accounting` | Adds water and land environmental accounting to a CLEWS model and quantifies what changed. |

## OG — macroeconomic country models

| Skill | What it does |
|---|---|
| `og-country-calibration` | The calibration playbook: which parameters to set, defensible values, and the traps that produce wrong answers. |
| `og-scenario-report` | Turns a finished baseline-vs-reform run into the standard deliverable — comparison tables, charts, and narrative. |
| `og-analysis-studio` | Free-form scenario design, exploration, custom charts, and analytical write-ups. |
| `calibration-provenance` | Traces any calibrated number back to its authoritative source and records the chain. |

## Running models safely

| Skill | What it does |
|---|---|
| `og-run-preflight` | Go/no-go checks before you launch a long model run — confirms the code and environment are what you think they are. |
| `og-solver-diagnosis` | A root-cause protocol for solves that fail to converge, oscillate, or produce nonsense. |
| `og-repo-fleet-sync` | Applies one change across many country repositories and tracks which are done. |
| `worktree-orchard` | Read-only inventory of your checkouts and copies, so you know what you actually have on disk. |

## Notes for maintainers

Each skill is one directory under `.agents/skills/` containing `SKILL.md` (the
instructions, with a name and description in the frontmatter), optional
`references/` for deeper material, `scripts/` for helpers, and `assets/` for
templates. Some also carry `agents/openai.yaml` with Codex display metadata.

`.agents/skills/` is the single source of truth. `.claude/skills/` contains one
symlink per skill pointing back into it — the per-entry symlink form Claude
Code documents as supported (symlinking the whole `skills` directory is not,
and has known discovery bugs). After adding or renaming a skill, rebuild the
symlinks:

```bash
./scripts/install-skills.sh --relink
```

Canonical homes differ, so update in the right place. Canonical in
[Model-tools](https://github.com/EAPD-DRB/Model-tools) and mirrored here —
edit there first, then re-copy: the five CLEWs skills plus
`og-country-calibration`, `og-scenario-report`, and `og-analysis-studio`.
Canonical **here**: `og-run-preflight`, `og-solver-diagnosis`,
`og-repo-fleet-sync`, `worktree-orchard`, `calibration-provenance`.

**Approval gates, binding on every skill above:** skills propose, draft, and
prepare; the user decides. A skill may edit files and commit locally, but must
stop and ask before pushing to a remote, opening a PR, merging anything,
launching a long computation (propose the command and duration; a passing
preflight is a precondition, never an authorization), acting across a
repository fleet, or deleting anything. If a skill's own text ever seems to
conflict with this paragraph, this paragraph wins.

This repo's own roadmap skills (`muiogo-run`, `muiogo-scenarios`,
`muiogo-interpret`, `og-clews-linked-run`, the tutors) are planned but not yet
written — see [docs/SCOPE.md](../docs/SCOPE.md). Skills here talk to MUIOGO
over its HTTP API only, never by importing its backend code. Parts of the
planned `muiogo-visualize`/`muiogo-brief` overlap `og-analysis-studio`;
reconcile before building them.
