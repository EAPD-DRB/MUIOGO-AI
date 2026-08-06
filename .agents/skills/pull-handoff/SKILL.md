---
name: pull-handoff
description: Bootstrap or pull the official Fiji and Philippines model repositories, safely unzip their current MUIO cases into ignored repository-local working trees, and maintain relative MUIOGO DataStorage symlinks. Use for a pristine MUIOGO setup or an existing two-laptop handoff.
---

# Pull Handoff

Pull and unzip. Do not solve, validate, or change model inputs as part of this
skill.

## Scope

Resolve MUIOGO by its Git remote and use its parent directory as the local
workspace. Operate only on the countries the user requests; use both when the
request says to update the full handoff. The official public remotes are:

- `https://github.com/EAPD-DRB/CLEWs-FJI.git`
- `https://github.com/EAPD-DRB/CLEWs-PHL.git`

Read applicable `AGENTS.md` files after locating or cloning each repository.

## Workflow

1. Locate each requested country repository among MUIOGO's siblings by its
   `origin` remote, not only by folder name. If it is missing, clone its
   official remote into the unused sibling path `CLEWs-FJI` or `CLEWs-PHL`.
   Before cloning, require that the destination does not exist; never clone
   over a file, directory, symlink, or partial checkout. After cloning, verify
   the canonical `origin`, checked-out default branch, and clean status. Stop
   if MUIOGO cannot be identified or an expected path is occupied.
2. Inspect the branch, upstream relation, and working-tree status of every
   existing or newly cloned country repository. Pull only a clean, behind
   branch with `git pull --ff-only`. Stop on local changes, conflicts, or
   divergence. Never reset, clean, rebase, force-update, or overwrite local
   work. A fresh clone already at its upstream revision needs no extra pull.
3. Select the current archive named in each country repository's current-model
   documentation. Never infer it from filename sorting.
4. Verify the documented SHA-256 when available, run `unzip -t`, reject unsafe
   paths, require one top-level case folder containing `genData.json`, and
   verify its directory name matches `osy-casename`.
5. Require `/case/` to be ignored by the country repository. Install the
   archive as `<country-repository>/case/<case-name>`, never as a tracked
   working tree. Extract to a temporary directory first. If the existing
   local case differs in non-result content, move the complete old case to
   `case/.backups/<case-name>-<timestamp>` before installing. If it matches,
   leave it intact so local results are not discarded.
6. Maintain `MUIOGO/WebAPP/DataStorage/<case-name>` as a relative symlink to
   the repository-local case. Leave a correct link unchanged. Before replacing
   a real directory, broken link, or wrong link, move it recoverably under
   `case/.backups/`; never delete it. Verify that the final link resolves to
   the intended case and that `osy-casename` matches its directory name.
7. If the result-free ZIP omitted empty run directories, recreate the empty
   `res/<run>/csv` directories declared by `view/resData.json` inside the
   repository-local case.

Do not solve, run validation, reconstruct provenance, or edit the model.

Report repositories cloned and pulled, repository-local case paths, relative
symlink targets, archive hashes, backup paths, and any repository skipped
because of local changes or an occupied clone destination.
