---
name: muiogo-provision
description: Add models and data to a MUIOGO installation and get them out again — install an OG country model, import a MUIO case archive or an Excel workbook, export a case as a shareable zip, check what is installed, and validate a case's inputs before a long solve. Use when asked to install, add, or set up a country or model; to import, upload, load, or bring in a case, archive, workbook, or dataset; to export, back up, download, or share a whole case or model; or to list what is installed. Also use to run MUIOGO's mechanical input-consistency checks before a long solve — for structural quality use clews-model-review, and for whether a model is calibrated well enough use assess-clews-calibration. For the EAPD Fiji/Philippines laptop-to-laptop flow specifically, prefer pull-handoff and push-handoff.
---

# Add models and data to MUIOGO, and get them out

Orient first with `muiogo status` (see `muiogo-workspace`) — it lists what is
already installed, so you do not install something twice.

## Before installing anything: is it already here?

Most people already have MUIOGO and some country models checked out. A country
model is one to three gigabytes, and a second copy is worse than none — the
tooling can end up pointing at whichever one you did not mean.

```bash
muiogo adopt --scan      # list existing checkouts, change nothing
muiogo adopt --auto      # record them as the workspace, installing nothing
```

Adopt first, install only what is genuinely missing.

## What is already here

```bash
muiogo cases                # CLEWs cases installed
muiogo og catalog           # OG country models available, marked when installed
muiogo og installed         # OG country models on this machine
```

`muiogo og catalog` reads the upstream register live, so it is current rather
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
muiogo og install --key og-zaf --wait
```

This goes through MUIOGO's own installer layer, which wraps the upstream OG-Core
universal installer. Do it this way rather than cloning by hand: the model lands
where MUIOGO, the OG-CLEWs link and every skill expect it, gets its **own
virtual environment**, and is recorded in MUIOGO's registry.

It is a long install — a full model environment, minutes not seconds. `--wait`
polls; without it, check progress with `muiogo og installed`. Propose it and let
the user decide before starting.

Two things to say afterwards, because they bite later:

- A freshly installed country model is a **single-industry** calibration. Coupled
  OG-CLEWS energy work needs multi-industry — see `og-clews-linked-run` for how
  that surfaces, and `og-run` for building it.
- Installing the model is not calibrating it. `og-country-calibration` is the
  playbook for making it defensible for a country.

For a country not in the catalogue, `--repo-url` (with optional `--branch`)
installs from a git URL.

## Importing a CLEWs case

To bring in a MUIO case archive — your own country model, a colleague's, or one
from a CLEWs country repository:

```bash
muiogo import --zip Philippines_v12.zip
```

The archive must hold **one top-level case folder containing `genData.json`**.
This uses the same validated path as the web interface's restore, so version
checks and post-import fixups all apply. The command reports the case name that
appeared, and fails loudly if none did — never assume an import worked because
the command returned.

Then confirm and check it before trusting it:

```bash
muiogo cases                                   # the new case is listed
muiogo scenarios --case "<new case>"           # scenarios and runs came across
```

For an Excel workbook into an existing case:

```bash
muiogo import --xls demand-update.xlsx --case "My Case"
```

**Importing a case that already exists will not silently merge.** If a case of
that name is installed, say so and agree with the user what to do — rename,
replace, or import alongside. For the EAPD Fiji and Philippines handoff
workflow specifically, `pull-handoff` already does this properly, with checksum
verification and a timestamped backup of the case being replaced; prefer it when
that is the situation.

## Exporting and sharing

```bash
muiogo export --case "My Case" --out ./share
```

That writes a self-contained `.zip` a colleague can import with
`muiogo import --zip`. It is also the right thing to do **before** any
destructive change — a scenario edit or a re-run cannot be undone.

For publishing a case back to its country repository with a handoff note and an
audit trail, use `push-handoff` instead; it packages, checksums, and records
provenance the way the team expects.

## Validating inputs before a long solve

```bash
muiogo validate --case "My Case" --run REF
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

1. `muiogo import --zip` the CLEWs case, or `pull-handoff` for the EAPD repos.
2. `muiogo validate` it, then `clews-model-review` it.
3. `muiogo og install --key og-<iso3>` for the macro side, if needed.
4. `og-country-calibration` to make that calibration defensible.
5. `muiogo-scenarios` to build policy scenarios, `muiogo-run` to solve.
6. `muiogo export` a copy before anyone edits anything further.

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
what you are about to change and where it will land.
