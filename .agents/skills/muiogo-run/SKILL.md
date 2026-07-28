---
name: muiogo-run
description: Run CLEWs/OSeMOSYS models in MUIOGO headless and collect their results — start and stop the server, solve one run or a batch, detect and diagnose failed solves, and save result CSVs reproducibly. Use when asked to run, solve, execute, or re-run a CLEWs case or scenario; to run several runs at once; to check whether a run succeeded or why it failed; to fetch or export the results of a run; or when another skill needs a case solved before it can proceed.
---

# Run CLEWs models in MUIOGO and collect results

Everything here goes through the `muiogo` command line, which drives MUIOGO's
HTTP API — the same path its web interface uses, so a headless solve and a
clicked solve produce identical results.

If you do not yet know where MUIOGO is installed, orient first with
`muiogo status` (see the `muiogo-workspace` skill). Take all paths from there.

## The loop

```bash
muiogo status                                   # is a server running? which cases exist?
muiogo serve                                    # start one if not (foreground; leave it running)
muiogo cases                                    # exact case names — they contain spaces
muiogo scenarios --case "CLEWs Demo"            # what runs already exist
muiogo run --case "CLEWs Demo" --run REF        # generate input + solve
muiogo results --case "CLEWs Demo" --run REF --out ./ref-results
```

`muiogo run` regenerates the model input from the case's current parameter data
and then solves, so it always reflects edits you have made. It prints:

```
status: success
Result - Optimal solution found - Total time (CPU seconds):       1.06
```

## Starting and stopping the server

`muiogo serve` runs in the foreground and holds the terminal. Start it in the
background so you can keep working, and always confirm it answered:

```bash
muiogo serve > /tmp/muiogo-server.log 2>&1 &
sleep 5
muiogo status          # must show: server  running — N case(s)
```

Stop it when the work is done:

```bash
kill $(lsof -ti :5002)          # use the port muiogo status reported
```

Two things to know. The port comes from the installation, not always 5002 —
`muiogo status` prints it and every command defaults to it. And MUIOGO solves
synchronously: one solve occupies the server, so do not fire runs in parallel
against a single server; use `muiogo batch` instead.

## Solvers

Use **CBC**, the default. It preprocesses the model input, builds the LP, and
solves. `--solver glpk` is broken in MUIOGO itself (it skips preprocessing and
fails on `MODEperTECHNOLOGY`) — tracked as MUIOGO issue #468. If a user asks for
GLPK, say it is a known upstream defect and use CBC.

Solve time scales with the model. The demo case takes about a second; a real
country case with many technologies, timeslices, and years can take minutes to
hours. For anything you expect to run long, propose it and let the user launch
it — that is an approval gate, not a formality.

## Running several

```bash
muiogo batch --case "CLEWs Demo" --runs REF,CO2TAX,RETRG
```

The batch endpoint generates input and solves each run server-side with CBC, and
reports total elapsed time. It is the right tool for a scenario matrix. Verify
afterwards — a batch reports overall status, so check each run individually:

```bash
for r in REF CO2TAX RETRG; do
  echo "$r: $(muiogo results --case "CLEWs Demo" --run $r | wc -l) result files"
done
```

## When a solve fails

A failed solve is not an exception you should swallow — it is the finding.
`muiogo run` reports the failure and the solver's own message.

Check, in this order:

1. **The command's output.** The status line and solver message say most of it.
2. **The log**: `muiogo log --case "<case>" --run <run>`.
3. **On disk**: no `res/<run>/csv/` directory means the run produced nothing.
   `res/<run>/results.txt` carries the raw solver output; its first line is the
   status.

Common causes and what they mean:

| Signal | Cause |
|---|---|
| `no value for MODEperTECHNOLOGY[...]` | GLPK path — switch to CBC (see above) |
| `Infeasible` / `problem is infeasible` | the model cannot meet demand under its constraints — a data problem, not a solver problem |
| `Unbounded` | a missing cost or capacity limit lets something grow freely |
| solver binary not found | GLPK/CBC not installed; `muiogo status` shows solver availability |
| no results and no message | check the server log; the server may have stopped |

For infeasible or otherwise suspicious models, hand off to
`clews-model-review` (structure and data consistency) rather than guessing at
the data yourself.

## Provenance: making a number defensible

Every solve writes a `RUN.json` beside its results recording the objective, a
SHA-256 of the generated model input, a SHA-256 over all result CSVs, which
scenarios were active, the solver, and the MUIOGO version. You do not have to do
anything to get it; `muiogo run` prints a one-line summary.

This matters because the pipeline is bit-deterministic but not self-auditing.
Solving the same run twice gives the same objective and byte-identical results —
but stored results can silently disagree with the case they live in. MUIOGO's own
demo ships a CO2TAX result of 600,590 tonnes that the shipped input data
reproduces as 513,337.

So, before you rely on a number you did not just produce:

```bash
muiogo verify --case "<case>" --run <run>              # does the record still match disk?
muiogo verify --case "<case>" --run <run> --resolve    # re-solve and prove it reproduces
```

`--resolve` re-solves and compares the objective and the results hash; it prints
"Reproduced exactly" or tells you the input data has changed. `muiogo compare`
also warns on its own when a run in the comparison has no provenance record.

Rule of thumb: **if a comparison matters, every run in it should have been solved
by you, from the same input state.** Re-solve the ones that were not.

## Saving results reproducibly

```bash
muiogo results --case "<case>" --run <run>              # list the result files
muiogo results --case "<case>" --run <run> --out DIR    # download all of them
```

Results are one CSV per output variable in tidy long format — `NewCapacity.csv`
is `r,t,y,NewCapacity`; `AnnualTechnologyEmission.csv` is
`r,t,e,y,AnnualTechnologyEmission`. Dimension letters follow OSeMOSYS: `r`
region, `t` technology, `f` fuel, `e` emission, `y` year, `l` timeslice, `m`
mode, `s` storage.

When you save results for later analysis, make the directory self-describing so
the numbers can be traced back: name it for the case and run, and record what
produced it.

```
<somewhere>/<case>-<run>-<date>/
  csv/                     the downloaded result files
  RUN.json                 written automatically: objective, input and results
                           hashes, active scenarios, solver, MUIOGO ref
  NOTES.md                 why you ran it and what you concluded
```

Never edit a file under `res/` by hand. Re-running a run deletes its previous
results first, so if a comparison matters, download before re-running.

## Handing off

- Interpreting, comparing, or charting what you just ran → `muiogo-analyze`.
- Creating a new scenario or combination to run → `muiogo-scenarios`.
- The model will not solve and you suspect its structure → `clews-model-review`.
- OG-Core solves are a different family entirely and are not run through
  `muiogo` — see `og-run-preflight` before launching one.

## Approval gates

Propose, draft, and prepare; the user decides. You may run short solves and save
results. Stop and ask before launching a long computation (propose the command
and expected duration), deleting a case or a run, or pushing, PR-ing, or merging
anything.
