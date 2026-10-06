---
name: push-handoff
description: Packages the repository-local Fiji and Philippines MUIO working cases as archives without solver results, verifies their MUIOGO symlinks, archives and recorded hashes, and commits and pushes the intended country-repository changes. Use when sending a two-laptop handoff or publishing a new case version to CLEWs-FJI or CLEWs-PHL; pull-handoff is the receiving side.
---

# Push Handoff

Zip and push. Do not rebuild, validate, solve, or redesign a model as part of
this skill.

## Scope

Resolve the sibling `MUIOGO`, `CLEWs-FJI`, and `CLEWs-PHL` repositories by
their Git remotes. Read applicable `AGENTS.md` files before acting.

## Workflow

Two of these steps need judgment. The rest are predicates with yes/no answers,
and `verify.py` decides them — it is faster and more reliable than checking by
hand, and it never gets bored on the eleventh check.

1. **Judgment — name the case and the archive.** Read the country
   repository's current-model documentation, unless the user names them
   explicitly. Never infer the current archive from filename sorting: the
   newest-looking name is routinely a control run or a predecessor kept for
   reference. If two archives could plausibly be the destination, ask.
2. **Is there anything to send?** Compare the live case with the current archive
   by content, not modification time, leaving out `res/` and every regenerated
   file listed in step 3. A difference only in generated files is not a model
   change: if neither the editable inputs nor the documentation changed, skip
   this country and report it unchanged. If they did change, confirm that
   permanent parameter edits are in the source JSON and that structural edits
   went through `genData.json` and MUIO's `UpdateCase`, not only into generated
   files.
3. **Export.** Zip the repository-local case as one ZIP with one top-level
   case folder, excluding `res/`, solver CSVs and logs, `data.txt`,
   `data_processed.txt`, LP files, and caches. Keep every editable parameter
   JSON, case-local documentation, and `view/` metadata — exclude by rule, so
   file types nobody has invented yet still ship. Give it a new versioned
   archive name; never overwrite a published archive. If the case's validation
   status is unknown or incomplete, say so in the archive's README entry and
   label it work in progress, and do not make it the recommended archive (this
   skill records the status; it does not run validation). Update the
   documentation that names the current case and archive, usually the
   repository `README.md` and `CURRENT_MODEL.md`: `pull-handoff` reads it to
   decide what to install. Then update **every** place
   the hash is written down, computing it from the archive you just built and
   never copying an earlier line. There is usually more than one: a
   `SHA256SUMS` beside the archive, sometimes another at the package root with
   repo-relative paths, and the `README.md` a recipient actually reads. Step 4
   finds them all — if it names a file you did not update, update it.
4. **Verify.** Fetch first — `verify.py` never fetches, because a verifier
   that mutates the repository it is judging cannot be run freely, so its
   upstream comparison is only as good as your refs. Run this for **each**
   country repository you are updating, with `verify.py` from this skill's
   folder (its path depends on where the skill is installed):

   ```bash
   git -C <country-repository> fetch
   python <this skill>/verify.py --repo <country-repository> --case <case-name>
   ```

   It checks the branch and upstream (and fails if the refs are more than 15
   minutes old), that the live case is gitignored and present, that the MUIOGO
   DataStorage entry is a symlink resolving to that exact case, that
   `osy-casename` agrees with the folder name **both in the live case and
   inside the archive**, that the archive holds one correctly-named top-level
   folder with no excluded results and an intact CRC, and that every recorded
   copy of the hash — in any checksum file or README anywhere in the
   repository — describes *this* archive. Add
   `--archive` when the path is ambiguous, `--datastorage` when MUIOGO is not
   a sibling, `--max-fetch-age 0` only when genuinely offline. **Exit 1 or 2
   stops the handoff.** Report what failed; do not work around it.
5. **Judgment — review and commit.** Read the diff yourself. Stage only the
   intended country-model files and archive, preserving unrelated local work,
   then re-run with `--staged` to confirm nothing else rode along:

   ```bash
   python <this skill>/verify.py --repo <country-repository> --case <case-name> --staged
   ```

   Use `--allow <path>` for a file you deliberately included. Then commit and
   fetch. **Before pushing, show the user the commit and the archive name and
   hash, and wait for a yes.** Then push normally. Never reset, rebase,
   force-push, or overwrite a published release.

Copy this and work through it for each country:

```
- [ ] 1. Case and archive named from the current-model documentation.
- [ ] 2. Something changed outside generated files. If not: report unchanged, stop.
- [ ] 3. Exported under a new versioned name; current-case documentation and every
         recorded hash updated.
- [ ] 4. verify.py passes. If it fails: fix the archive, documentation or hashes,
         go back to step 3 for those, and verify again.
- [ ] 5. Only intended files staged; verify.py --staged passes. If not: unstage,
         go back to step 5.
- [ ] 6. User has seen the commit, archive name and hash, and said yes. Push.
```

Do not create a HANDOFF note, reconstruct provenance, run model validation,
or change model inputs. Those are separate modelling tasks and must be
requested separately.

Report the live case and verified symlink, archive path and SHA-256, commit,
pushed branch, and any repository skipped because it was unsafe to update.
