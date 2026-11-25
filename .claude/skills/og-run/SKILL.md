---
name: og-run
description: >-
  Installs and runs an OG-Core model (OG-Core or a country repo such as OG-USA, PHL, ZAF, IDN, BRA,
  ETH) the way its users do, checks the environment before a run, monitors it and collects the
  output with its provenance. Use when asked to run, solve or re-run an OG model, produce a
  baseline or reform, test or benchmark a code change, or check whether the model fails, or when
  another task needs OG output that does not exist yet. Calibrating is og-country-calibration; a
  failing solve is og-solver-diagnosis; presenting results is og-scenario-report.
---

# Run an OG-Core model

## Running the model

Install each model with OG-Core's installer, one copy per commit, and run the repo's example script
unchanged from that copy's environment. Tuning uses the repo's own tuning script, and tests run in
such a copy with the repo's own test command. A run outside this path cannot be reproduced or
compared, so its numbers do not count; to investigate, read the saved output. A baseline takes
under ten minutes. Record with every result the repo, commit, ogcore version, script and whether
it ran online. Detail, and what to do when it is tempting to step off this path:
[og-run-rules.md](references/og-run-rules.md).

An OG solve takes minutes, uses parallel worker processes, and has two stages (steady state, then
transition path). Say what you are about to run and how long it should take before starting it.

## Install

Follow `scripts/QUICK_INSTALL.md` in OG-Core:

```bash
curl -fsSL https://raw.githubusercontent.com/PSLmodels/OG-Core/master/scripts/install.sh -o install.sh
mkdir -p <new parent folder>
bash install.sh --repo <key> --dest <new parent folder> --yes     # --list shows the keys
# a branch, fork or local clone, into its own folder:
bash install.sh --repo-url <git URL or clone> --branch <branch> --dest <another new folder> --yes
```

The installer clones the repo, runs `uv sync --extra dev` and checks the import. Create the parent
folder first and run the installer from it, so its log sits beside the copy. Use a new folder for
every commit; never install over a checkout that holds someone's work.

The installer names the package from the last part of the URL (lowercased, hyphens dropped) and
checks that it imports, so install from a clone whose folder is named like the repo (`OG-<XXX>`),
not from a worktree or a folder such as `OG-<XXX>-demo`, which installs but fails the import check.
A copy is tied to the commit it cloned: when the branch moves, install the new commit into a new
folder rather than pulling inside the copy.

## Check before a run

Confirm the run will use the code you mean:

- the branch and commit of every repo involved are the ones the task names;
- the model's interpreter (`<copy>/.venv/bin/python`) imports the country package and ogcore from
  inside that copy, from the folder the run starts in;
- the entry script is the repo's own example or tuning script, unchanged (`git status` clean), with
  nothing on `PYTHONPATH`;
- the packaged parameters load against the installed ogcore.

`scripts/preflight.py` (standard library only, read-only) does these checks in one call and prints
GO or NO-GO:

```bash
python3 scripts/preflight.py \
  --check <copy>/OG-PHL::ogphl,ogcore \
  --run-cwd <copy>/OG-PHL \
  --entry-script <copy>/OG-PHL/examples/run_og_phl.py \
  --params-json <copy>/OG-PHL/ogphl/ogphl_default_parameters.json
```

For a coupled run with a second environment (ogclews-link), pass one `--check` per environment,
with the OG side's interpreter from the model registry; the link's environment must not import
ogcore. A NO-GO names what to fix; fix the environment rather than working around it with
`sys.path` or `PYTHONPATH`. If a fresh run reproduces a number from a run known to be buggy, assume
the wrong code ran and check again before using it.

## Launch

Country repos ship example scripts that define the baseline and the reform; list `examples/` to
see them (`run_og_<xxx>.py`, and a multi-industry script on some branches). They take no
arguments. From the installed folder:

```bash
cd <copy>/OG-PHL
source .venv/bin/activate
python examples/run_og_phl.py          # or: uv run python examples/run_og_phl.py
```

The script starts `min(cpu_count, 7)` workers, solves the baseline into
`examples/<...>/OUTPUT_BASELINE/`, applies the reform, solves it into `OUTPUT_REFORM/`, and stops
the workers. Each stage writes `SS/SS_vars.pkl`, `TPI/TPI_vars.pkl` and `model_params.pkl`.

Solver settings belong in the repo's packaged parameters: `TPI_outer_method="anderson"` and `nu`
0.2 or lower (some repos set Anderson but leave `nu` at 0.4). If the repo does not set them, run the
example as shipped and say so.

Things that bite in a session with no one at the keyboard:

- **The UN population token.** ogcore looks for it in order (check `ogcore/demographics.py` in your
  build): the `un_token` argument, `UN_API_TOKEN`, a per-user file (managed with `og-token`), a
  `un_api_token.txt` in the working folder (deprecated), then prompts when interactive or falls back
  to the EAPD-DRB Population-Data archive. A run that hangs early with no output:
  check this first.
- **Live data.** When online, some examples call `Calibration(p, update_from_api=True)`, which can
  overwrite curated values. Say whether the run was online.
- **`uv run` re-syncs to the lockfile.** In an installer copy that changes nothing. Where ogcore
  differs from the lockfile, `uv run` silently swaps it; use `.venv/bin/python` and check
  `ogcore.__version__, ogcore.__file__` first.

For a long run, start it in the background with output to a log, and monitor rather than
relaunching:

```bash
nohup .venv/bin/python -u examples/run_og_phl.py > run.log 2>&1 &
```

- **Finished?** The transition logs `Time path iteration complete.` at the end.
- **Healthy?** Add up the CPU of all worker processes: during the transition they should keep the
  machine nearly full. One busy worker while the others wait points to a straggler
  (og-solver-diagnosis, class N).
- **On time?** Past about ten minutes for a baseline, check the setup before waiting longer.

To solve a different scenario, copy the example and change only the reform's parameters, the solver
settings or the output folder, keeping its structure (worker pool, calibration call, runner); say
what changed.

## Multi-industry runs

A freshly installed country model is single-industry. Coupled OG-CLEWS work needs multi-industry,
because a single-industry model has no electricity industry for an energy price to act on. The
calibrated multi-industry script usually lives on a repo's multi-industry branch; the default branch
may carry only a demo under a similar name. Check what it loads, and use
og-multi-industry-calibration to judge whether the calibration is real. It may first solve its
steady state by continuation, and baseline plus reform take tens of minutes.

## Testing a code change

For a change to a country repo or to OG-Core itself: commit it on a branch, install that branch into
its own folder, and run the example there; install the base the same way and compare the saved
outputs. Tests run in the same installed copies with the repo's own command (CI's `-m "not local"`,
or `-m local` for the slow ones). Run one solve at a time when you compare timings.

To test an unreleased OG-Core under a country model, pin it on a branch of the country repo
(`[tool.uv.sources]` with the commit, `uv lock`, commit) and install that branch; installing it into
an existing copy runs something nobody else can reproduce (og-solver-diagnosis, "Running against an
unreleased ogcore").

To check that an OG-Core change keeps the country models working:

1. **Can each country load on both sides?** Check each country's packaged parameters against the
   base and the changed ogcore (`--params-json` above). A country that does not load on one side
   cannot be compared; report it.
2. **Which base?** The commit the change starts from, not today's master, so that unrelated upstream
   changes stay out of the comparison.
3. **Same inputs on both sides:** run offline (`update_from_api=False`).
4. **Does the run reach the changed code?** A baseline may never touch it; add a reform that does.

Report per country the expected value, the base and the change, with the resource-constraint
error in the first period and after. A run that fails or differs goes to og-solver-diagnosis.
Writing the PR follows the repo's own contribution conventions.

## Collecting the results

A completed run leaves `OUTPUT_BASELINE/` and `OUTPUT_REFORM/`. Keep them together, write the
provenance next to them (repo, branch, commit, ogcore version, script, parameters changed, online
or not, date), and never edit files inside them; to redo a run, re-solve.

## When a solve misbehaves

A run that dies at once is almost always the environment (interpreter, branch, data): check again.
One that will not converge, oscillates or returns implausible numbers has a diagnosable cause: use
og-solver-diagnosis rather than re-running on a guess.

## Related skills

og-country-calibration (which parameters to set and why), og-scenario-report (designing reforms,
presenting results), og-solver-diagnosis, og-clews-linked-run (coupling to the energy system; it ships with MUIOGO-AI). Inside
a MUIOGO installation, start with muiogo-workspace to find the installed models.
