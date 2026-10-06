---
name: muiogo-provision
description: Adds models and data to a MUIOGO installation and gets them out again - installs and updates OG country models, imports MUIO case archives, CLEWs country repositories and Excel workbooks, exports a case as a shareable zip, and runs MUIOGO's input checks before a long solve. Use when asked to install, update, import, load, export, back up or share a model or case, to list what is installed, or to validate a case's inputs.
---

# Add models and data to MUIOGO, and get them out

Orient first with `muiogo-ai status` (see `muiogo-workspace`) — it lists what is
already installed, so you do not install something twice.

## Which world

Everything below acts on ONE world — the installed runtime, reached through the
pinned launcher `muiogo-ai`. Never bare `muiogo` (the one exception, `muiogo adopt`,
is below), and never fall back to it.
Every command prints a `world:` line to stderr first: read it, and name that
world when you tell the user what is installed, or what you imported, exported or
validated. Exit code 3 means the command refused a world crossing — stop, do not
sidestep it. Full rules: `../WORLD_DISCIPLINE.md`.

## Before installing anything: is it already here?

A country model is one to three gigabytes, and a second copy is worse than none:
the tooling can end up pointing at whichever one you did not mean. Check what
this installation already has (next section) before installing anything.

The user may also have their own checkouts, which they run by hand. That is a
separate setup, the *adopted* one, reached by bare `muiogo` on port 5002.
`muiogo adopt --scan` lists those checkouts and changes nothing; `muiogo adopt
--auto` records them as the adopted setup. It is the one bare `muiogo` command
these skills use (see `muiogo-workspace`), and it is the user's setup, so propose
it and let the user say yes. Adopting changes nothing in this installation: a
model missing here still has to be installed here.

## What is already here

```bash
muiogo-ai cases              # CLEWs cases installed
muiogo-ai og catalog         # OG country models available, marked when installed
muiogo-ai og installed       # OG country models on this machine
```

`muiogo-ai og catalog` reads the upstream register live, so it is current rather
than a list someone maintained by hand:

```
  og-core      CORE  base model (no country calibration)
  og-eth       ETH   Ethiopia
  og-zaf       ZAF   South Africa
  og-idn       IDN   Indonesia
  og-phl       PHL   Philippines                       installed
  og-bra       BRA   Brazil
```

## Installing an OG country model

```bash
muiogo-ai og install --key og-zaf --wait
```

This goes through MUIOGO's own installer layer, which wraps the upstream OG-Core
universal installer. Do it this way rather than cloning by hand: the model lands
where MUIOGO, the OG-CLEWs link and every skill expect it, gets its **own
virtual environment**, and is recorded in MUIOGO's registry.

It is a long install — a full model environment, minutes not seconds. `--wait`
polls; without it, check progress with `muiogo-ai og installed`. Propose it and
let the user decide before starting.

Two things to say afterwards, because they bite later:

- A freshly installed country model is a **single-industry** calibration. Coupled
  OG-CLEWS energy work needs multi-industry — see `og-clews-linked-run` for how
  that surfaces, and `og-run` for building it.
- Installing the model is not calibrating it. `og-country-calibration` is the
  playbook for making it defensible for a country.

For a country not in the catalogue, `--repo-url` (with optional `--branch`)
installs from a git URL.

### Updating an installed model

On a MUIOGO that has the OG-Core page, "Check for updates" (the refresh icon on
the card, or `refreshCalibration` with `check_only: true`) only reports. It cannot
apply the update: every model the installer set up is registered from a local
folder, and MUIOGO refuses to pull over local folders. The card says "update the
local folder to get this version" and nothing more, so users get stuck here.

The supported way is the installer's update mode, run with the server stopped,
from the `MUIOGO-AI` checkout that installed this world. Copy this and work
through it:

```
- [ ] muiogo-ai stop
- [ ] ./scripts/install.sh --update
- [ ] Read its report for every model: the version it moved from and to, or why
      it skipped one (uncommitted changes, or no tracking branch: someone's
      development copy). If it skipped a model the user expected updated, stop
      and report that; do not force it.
- [ ] muiogo-ai serve --detach, then confirm with muiogo-ai og installed.
```

It fast-forwards each installed model, re-syncs its venv with the same flags
MUIOGO's installer uses (`uv sync --extra dev`), and re-registers it so the
registry's commit hash is current. Tell the user what changed.

Do not tell users to `git pull` and `uv sync` by hand: a plain `uv sync` strips
the dev tools, and "Check again" afterwards leaves the registry's commit hash
stale (see `docs/API_ENDPOINTS.md`). This is an installer job until MUIOGO
offers the Update button for installer-managed models.

## Importing a CLEWs case

To bring in a MUIO case archive — your own country model, a colleague's, or one
from a CLEWs country repository:

```bash
muiogo-ai import --zip Philippines_v12.zip
```

The archive must hold **one top-level case folder containing `genData.json`**.
This uses the same validated path as the web interface's restore, so version
checks and post-import fixups all apply. The command reports the case name that
appeared, and fails loudly if none did — never assume an import worked because
the command returned.

Where the MUIOGO behind the setup has the `/clews` install layer (MUIOGO PR
#519 or newer), prefer installing a country straight from its repository:

```bash
muiogo-ai clews inspect --repo-url https://github.com/EAPD-DRB/CLEWs-PHL
muiogo-ai clews install --repo-url https://github.com/EAPD-DRB/CLEWs-PHL
```

`inspect` shows the menu: every version the repository ships, newest first, with
the cases already on this machine marked. `install` takes the recommended version
and case unless you name others with `--vintage <id>` and `--case <name>`
(repeat `--case` for several). The server finds the versions by reading the
repository: a folder holding a `SHA256SUMS` file and MUIO archives is a version,
or the repository describes itself in a `clews-country.json`. It downloads the
case, verifies it against the published checksums (a mismatch installs nothing),
and imports it, recording provenance you can check later with `muiogo-ai clews
installed` and `muiogo-ai clews update-check`. Newer MUIOGO versions offer the
same from the browser: Home, then the download button.

Fall back to the zip import above when the command reports that the server has
no `/clews` layer, or when an older server finds neither checksums nor a
`clews-country.json` in the repository.

Then confirm and check it before trusting it:

```bash
muiogo-ai cases                                # the new case is listed
muiogo-ai scenarios --case "<new case>"        # scenarios and runs came across
muiogo-ai case-path --case "<new case>"        # where it landed, in this world
```

For an Excel workbook into an existing case:

```bash
muiogo-ai import --xls demand-update.xlsx --case "My Case"
```

**Importing a case that already exists will not silently merge.** If a case of
that name is installed, say so and agree with the user what to do — rename,
replace, or import alongside. For the EAPD Fiji and Philippines handoff
workflow specifically, `pull-handoff` already does this properly, with checksum
verification and a timestamped backup of the case being replaced; prefer it when
that is the situation.

## Exporting and sharing

```bash
muiogo-ai export --case "My Case" --out ./share
```

That writes a self-contained `.zip` a colleague can import on their own machine
with their own launcher (`muiogo-ai import --zip` on an installed setup). It is
also the right thing to do **before** any
destructive change — a scenario edit or a re-run cannot be undone.

For publishing a case back to its country repository with a handoff note and an
audit trail, use `push-handoff` instead; it packages, checksums, and records
provenance the way the team expects.

## Validating inputs before a long solve

```bash
muiogo-ai validate --case "My Case" --run REF
```

MUIOGO ships ten input-consistency checks — year splits summing to one, capacity
bounds not inverted, demand profiles summing to one, enough capacity to meet
activity floors, and so on. It reports `10/10 input checks passed`, or names the
failures.

Run this whenever a case is newly imported or heavily edited, and always before a
long solve. These failures are exactly what produce an infeasible model or a
quietly wrong answer, and catching them costs a second instead of an hour.

A pass is not a guarantee of a *good* model, only a consistent one. For
structure and data quality use `clews-model-review`; for whether it is calibrated
well enough to answer a question, `assess-clews-calibration`.

## A sensible order for a new country

Copy this and work through it:

```
- [ ] 1. muiogo-ai import --zip the CLEWs case, or pull-handoff for the EAPD
         repos, or muiogo-ai clews install from its repository.
- [ ] 2. muiogo-ai validate it. If any check fails: fix the named inputs and
         validate again; do not go on until every check passes.
- [ ] 3. clews-model-review it. If it reports a FAIL: fix it (clews-model-fix
         for structure), then back to step 2.
- [ ] 4. muiogo-ai og install --key og-<iso3> for the macro side, if needed.
- [ ] 5. og-country-calibration to make that calibration defensible.
- [ ] 6. muiogo-scenarios to build policy scenarios, muiogo-run to solve.
- [ ] 7. muiogo-ai export a copy before anyone edits anything further.
```

## Handing off

- The EAPD Fiji/PHL handoff flow, in either direction → `pull-handoff`,
  `push-handoff`.
- Building a CLEWs country model from scratch instead of importing one →
  `build-clews-model`.
- Calibrating the OG model you just installed → `og-country-calibration`.
- Solving, scenarios, analysis → `muiogo-run`, `muiogo-scenarios`,
  `muiogo-analyze`.

## Approval gates

Propose, draft, and prepare; the user decides. Listing and validating are free.
**Stop and ask before installing a country model** (a long download and build),
**before importing over an existing case**, and before deleting anything. Say
what you are about to change and where it will land — including which world.
Never install or import into the user's own checkouts unless they asked for
that; if a case is missing from the installation, report that rather than
reaching into theirs.
