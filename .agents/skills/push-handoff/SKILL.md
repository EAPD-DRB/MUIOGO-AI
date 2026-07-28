---
name: push-handoff
description: Prepare and push laptop-to-laptop handoffs for the EAPD Fiji and Philippines CLEWs models. Use when asked to publish, package, transfer, or hand off newer local Fiji/PHL MUIO cases, create a HANDOFF note, or commit changed skills in Model-tools.
---

# Push Handoff

Package reproducible Fiji and Philippines work, preserve its audit trail, and
push only reviewed changes.

## Scope

Resolve these sibling repositories from their Git remotes rather than assuming
a fixed home path:

- `MUIOGO`: installed cases under `WebAPP/DataStorage/`
- `CLEWs-FJI`: active case `Fiji_v2`
- `CLEWs-PHL`: active analysis case
  `Philippines_v12_ENV_LAND_WATER_DIAGNOSTIC`
- `Model-tools`: shared skills

Read every applicable `AGENTS.md` before acting.

## Workflow

1. Fetch each repository and print its branch, `HEAD`, upstream relation, and
   working-tree status. Never reset, force-push, move tags, or overwrite a
   published release archive. Stop on a behind/diverged branch or unresolved
   conflict.
2. Compare installed cases with the repository archive and packaged source by
   content, not modification time. Exclude `res/`, solver CSVs/logs,
   `data.txt`, `data_processed.txt`, LP files, and other regenerated outputs.
   A generated-file-only difference is not a model change.
3. If neither source inputs nor documentation changed, skip repackaging that
   model and report it unchanged.
4. For a changed model, confirm permanent parameter edits are in the source
   JSON and structural edits passed through `genData.json` plus `UpdateCase`.
   Run the repository's documented validation chain. If validation is
   incomplete, label the package as work in progress and do not replace the
   current recommended archive.
5. Update the audit trail before packaging:
   - the case's `MODEL_FIXES*.md`;
   - package `documentation/HISTORY.md`;
   - `CURRENT_MODEL.md`, `KNOWN_LIMITATIONS.md`, model/source maps, and
     calculation or assumption registers when affected;
   - `muio/README.md` and `SHA256SUMS`.
6. Create or refresh `HANDOFF-YYYY-MM-DD.md` in each changed model package.
   Record the branch and commit, case/archive version and SHA-256, changes
   since upstream, validation status, incomplete checks, exact continuation
   commands, artifact locations, and immutable baselines. Never call an
   imposed or stale result validated.
7. Use a new versioned archive name. Use the repository-native exporter:

   ```bash
   python CLEWs-FJI/Fiji_v2_CLEWs_calibration/scripts/export_muiogo_case.py \
     MUIOGO/WebAPP/DataStorage/Fiji_v2 <fiji-output.zip> --exclude-results

   python CLEWs-PHL/Philippines_v12_CLEWs_build/scripts/export_muiogo_case.py \
     MUIOGO/WebAPP/DataStorage/Philippines_v12_ENV_LAND_WATER_DIAGNOSTIC \
     <phl-output.zip>
   ```

8. Run `unzip -t`, verify the archive has one expected top-level case folder,
   and reject any `res/`, `data.txt`, `data_processed.txt`, LP, solver CSV, or
   solver-log entry. Keep required `view/` metadata. Recompute SHA-256 and
   reconcile every documented hash.
9. Review the diff, commit only the relevant model-package files, fetch once
   more, and push the tracked branch normally.
10. In `Model-tools`, commit and push changes under `skills/` when present.
    Stage only skill-related files and preserve unrelated work.

Report each repository as unchanged, committed, pushed, or blocked; list every
archive and hash; and state exactly which validation checks ran.
