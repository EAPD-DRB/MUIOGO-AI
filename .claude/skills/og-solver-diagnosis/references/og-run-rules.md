<!-- GENERATED FILE - do not edit here.
     Source: skills/shared/og-run-rules.md
     Regenerate: python scripts/sync_shared.py
     A local copy exists so this skill works when its directory is
     installed on its own, in Claude or in Codex. -->

# Running an OG model

Run the model the way its users do, so that every result can be reproduced and compared. If the
environment you work in has its own instructions on where models are installed and how to run
them (a project `AGENTS.md`, or a workspace skill such as MUIOGO-AI's muiogo-workspace), follow
them first; these rules still hold inside them.

- **Install** each model with OG-Core's installer, as `scripts/QUICK_INSTALL.md` in OG-Core
  describes, one fresh copy per commit. A branch, fork or local clone installs the same way
  (`--repo-url <URL> --branch <branch>`); an unreleased ogcore goes in through a branch of the
  country repo that pins it.
- **Run the repo's example script unchanged** (`python examples/run_og_<xxx>.py`) from that
  copy's own environment. Calibration tuning uses the repo's own tuning script, and tests run in
  such a copy with the repo's own test command.
- **Results come only from these runs.** A run outside this path cannot be reproduced or compared,
  so its numbers do not count, as evidence of a failure or of a fix. To investigate, read the saved
  output (`OUTPUT_BASELINE`, `OUTPUT_REFORM`, the log) with the installed package's functions.
- **Expect a baseline in under ten minutes:** the steady state in seconds to a minute or two, the
  transition in about 5–7 minutes, with all cores busy. Much longer means something is wrong
  (og-solver-diagnosis).
- **Solver settings live in the packaged parameters:** Anderson (`TPI_outer_method = "anderson"`)
  with `nu` 0.2 or lower. Validation runs are offline (`update_from_api=False`); check whether the
  example goes online and say so.
- **One model job on the machine at a time,** tests included: before launching, check that no other
  solve, test suite or heavy job is running (`uptime`, `ps`). Shared cores slow every job, make
  timings meaningless and can look like a stall.
- **Record with every result** the repo, branch and commit, the ogcore version, the script, any
  parameter changed and whether it ran online.

When it is tempting to step off this path:

| Situation | What to do |
|---|---|
| A quick check | Run the example's steady state, or the repo's tuning script, from the installed copy |
| A run fails or looks wrong | Read its saved output and log; og-solver-diagnosis |
| Testing a code change | Commit it on a branch, install that branch, run the example there |
| The environment has drifted from the lockfile | Re-run the installer into a new folder |
| The task seems to need a different setting or script | Ask the person you are working with, and report exactly what differed |

Installing and troubleshooting: og-run. A solve that fails or looks wrong: og-solver-diagnosis.
