---
name: pull-handoff
description: Bootstraps or pulls the official Fiji and Philippines CLEWs repositories, installs their current MUIO case into an ignored repository-local working tree, and keeps MUIOGO's DataStorage entry a relative symlink to it. Keeps or backs up local work and never deletes it. Use for a fresh MUIOGO setup or to receive a two-laptop handoff; push-handoff is the sending side.
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

One step needs judgment: naming the case. Everything after it — pull, verify,
unzip, link, restore run directories — is `install.py`, which prints what it
will do before it does anything.

1. **Clone, if the repository is missing.** Locate each requested country
   repository among MUIOGO's siblings by its `origin` remote, not by folder
   name. Clone the official remote into the unused sibling path `CLEWs-FJI` or
   `CLEWs-PHL` only if that path does not exist — never over a file,
   directory, symlink, or partial checkout. Then confirm the canonical
   `origin`, the default branch, and a clean status.
2. **Judgment — name the case.** Read the country repository's current-model
   documentation, unless the user names it. Never infer the current case or
   archive from filename sorting: the newest-looking name is routinely a
   control run or a predecessor kept for reference. If two archives could
   plausibly be the one, ask.
3. **Plan.** Run `install.py` from this skill's folder for each country
   repository (its path depends on where the skill is installed), and read the
   output:

   ```bash
   python <this skill>/install.py --repo <country-repository> --case <case-name> --pull
   ```

   It changes nothing without `--apply`. It reports what it would pull, which
   archive it resolved, whether it keeps the live case or moves it aside (and
   where), what it would do to the MUIOGO entry, and any reason it refuses to
   start. When the plan moves anything aside, show the plan to the user before
   applying.
   Add `--archive` when the archive path is ambiguous, `--datastorage` when
   MUIOGO is not a sibling, and drop `--pull` to install from what is already
   checked out. **Exit 1 or 2 stops the handoff.** Report what failed; do not
   work around it.
4. **Apply.** Re-run the same command with `--apply`.

   ```bash
   python <this skill>/install.py --repo <country-repository> --case <case-name> --pull --apply
   ```

   It fast-forwards with `git pull --ff-only` on a clean branch and stops on
   local changes or divergence; refuses to install unless `/case/` is
   gitignored; verifies the archive before anything moves — one correctly-named
   top-level folder, no excluded solver results, intact CRC, `osy-casename`
   agreeing with the folder name, and every recorded SHA-256 in the repository
   describing this archive; extracts to a temporary directory beside the target
   and moves it into place only once complete; maintains
   `MUIOGO/WebAPP/DataStorage/<case-name>` as a relative symlink and checks
   that it resolves; and recreates the empty `res/<run>/csv` directories named
   in `view/resData.json`.

   **It never deletes local work.** A live case whose files outside `res/`
   already match the archive is kept as it is, local solve results included. A
   live case that differs is moved to `case/.backups/<case-name>-<time>` before
   the new one goes in. A real folder, file or wrong link where MUIOGO's entry
   belongs is moved to `case/.backups/<case-name>-datastorage-<time>`: it may
   hold edits or results that never came from an archive. `case/` is gitignored,
   so backups stay out of git; tell the user where they are, and leave clearing
   them to the user. A failure at any point leaves the previous case in place.

   Skills installed or updated by the pull register on the next session start;
   tell the user to reload if they need them now.

Never reset, clean, rebase, or force-update a country repository.

Do not solve, run validation, reconstruct provenance, or edit the model.

Report repositories cloned and pulled, repository-local case paths, relative
symlink targets, archive hashes, every backup made and its path, and any
repository skipped because of local
changes or an occupied clone destination.
