---
name: MUIOGO-AGENT
description: Make reproducible changes to MUIOGO OSeMOSYS cases and validate them through the application generation, GLPK matrix-check, and CBC solve chain.
---

# MUIOGO model-change protocol

These instructions apply whenever changing or validating an OSeMOSYS case in this repository.

## Useful resources

- Consult the [OSeMOSYS model documentation](https://osemosys.readthedocs.io/en/latest/manual/Introduction.html) when model concepts, equations, parameters, or constraints need clarification.
- Consult the [OSeMOSYS/MUIO model code](https://github.com/OSeMOSYS/MUIO) when implementation details or the upstream model formulation need clarification.

## Source of truth

- Make permanent model changes only in the case's source parameter files. Examples include `RYC.json` for demand, `RYT.json` for capacity limits, `RYTM.json` for costs, and the appropriate `RY*.json` file for other parameters.
- Make structural changes, such as adding technologies or commodities, in `genData.json` and pass them through the application's `UpdateCase` workflow so all parameter JSON files are regenerated while existing values are preserved.
- Never make a permanent change directly in generated solver files such as `data.txt`, `data_processed.txt`, or an LP file. Such a change is not reproducible from the application and must not be promoted as a model fix.

## Required validation chain

1. Work on a disposable copy of the case. Do not overwrite the live case's `res/` outputs while testing.
2. Generate the solver input through the same application path used by the UI: call `DataFile(case).generateDatafile(run)` and then `.preprocessData()`.
3. Inspect the generated data and derived sets to confirm that the source edits survived export and that mappings such as `MODEperTECHNOLOGY` were built correctly.
4. Run `glpsol --check` to validate the matrix and emit the LP, then solve it with CBC through the normal model chain.
5. Compare the result with an appropriate unchanged baseline. At minimum, check solver status, objective value and percentage change, the specifically affected activities/capacities/emissions, relevant constraint residuals and duals, and unexpected changes elsewhere.
6. Verify result timestamps and case/version identity so stale or mismatched outputs are never treated as results of the new inputs.
7. Promote the source-file changes to the live case only after all required checks pass. Regenerate the live case through the application; do not copy a hand-edited generated file into it.

## Diagnostic exception

- A generated file may be modified only inside a disposable test area for a narrowly scoped A/B diagnosis, such as isolating a constraint responsible for infeasibility or poor solver performance.
- Clearly label this as a diagnostic experiment. Reproduce any accepted remedy in the source parameter files and repeat the complete application-generation and solve chain before treating it as a model change.

## Solve-time regression triage

- Treat a sudden solve-time regression as an incident. Inspect the latest source-parameter diff first, then test the smallest plausible rollback in a disposable copy before designing a new formulation.
- Establish one unchanged control and one minimal A/B variant. Use the last known-good runtime as the initial time budget; stop a regressed run after roughly twice that runtime unless its solver log shows credible convergence.
- When the minimal rollback restores an optimal solve, stabilize the case with that rollback and complete the required validation chain. Investigate ways to recover optional calibration detail as separate follow-up work.
- Treat identical positive activity bounds (`TAL = TAU`) as a high-risk calibration technique in CBC. They are mathematically valid, but every new use requires a dedicated solve-time A/B test against the unpinned case.
- Do not run a long sequence of alternative formulations during incident recovery unless the user explicitly prioritizes preserving the disputed formulation over restoring a working solve.

## Reporting

- Document every model change in the affected case's `MODEL_FIXES*.md` file before considering the work complete. If the case does not yet have one, create it using the case's existing naming convention.
- Each entry must record the reason for the change, the source files and parameters changed, the before/after formulation or values, the generated artifacts and baseline inspected, the validation results, and any incomplete checks or known limitations.
- Do not describe a change as fully validated if generation, preprocessing, matrix validation, CBC optimization, or baseline comparison is incomplete.
- Report exactly which checks passed, failed, timed out, or were not run.
- Preserve an audit trail of the source files changed, generated artifacts inspected, baseline used, and material result differences.
