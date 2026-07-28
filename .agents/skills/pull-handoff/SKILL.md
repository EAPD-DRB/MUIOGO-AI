---
name: pull-handoff
description: Pull and install the latest EAPD Fiji and Philippines CLEWs handoffs. Use when moving model work to another laptop, updating CLEWs-FJI, CLEWs-PHL, and Model-tools, or unpacking the current recommended Fiji and PHL MUIO archives into MUIOGO.
---

# Pull Handoff

Fast-forward the three handoff repositories and install clean, runnable MUIO
cases without discarding local work.

## Scope

Resolve sibling repositories by their remotes:

- `CLEWs-FJI`
- `CLEWs-PHL`
- `Model-tools`
- target checkout `MUIOGO`

Read applicable `AGENTS.md` files before acting.

## Workflow

1. For each of the three repositories, fetch `origin` and inspect branch,
   `HEAD`, upstream relation, and status. Pull only a clean, behind branch with
   `git pull --ff-only`. Never reset, clean, rebase, or overwrite local
   changes. Report and skip a dirty or diverged repository.
2. Select archives from repository documentation, not filename sorting:
   - Fiji: the current portable case named in
     `Fiji_v2_CLEWs_calibration/muio/README.md`;
   - Philippines: the most complete analysis case named in
     `Philippines_v12_CLEWs_build/muio/README.md`.
3. Verify the documented SHA-256 when available, run `unzip -t`, and require
   exactly one safe top-level case folder matching `genData.json`.
4. Install under `MUIOGO/WebAPP/DataStorage/`:
   - if the target is absent, extract it;
   - if its non-`res/` content matches the archive, keep it;
   - if it differs, move the whole installed case to a timestamped sibling
     backup, then extract the new case. Do not copy old results into the new
     model because they may be stale or mismatched.
5. Result-free ZIP files omit empty run directories. Read
   `view/resData.json` and create `res/<Case>/csv` for every configured run so
   MUIO can generate `data.txt`.
6. Verify the installed directory name and `osy-casename`, record repository
   `HEAD`s and archive hashes, and confirm no solver results were imported.
   Do not solve or alter model inputs as part of this skill.

Report which repositories changed, the installed case paths, any backup paths,
and any repository skipped for local changes. If `Model-tools` changed, tell
the user that Codex may need a reload before newly installed skills appear.

## Related skills

- `muiogo-provision` — the generic path: import any case archive, not just the EAPD ones.
- `muiogo-run`, `muiogo-analyze` — solving and reading what you just installed.

These live in the MUIOGO-AI collection; if one is not available to you,
do the job directly and say which skill would have covered it.
