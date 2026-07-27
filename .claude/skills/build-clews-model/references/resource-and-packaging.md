# Resource estimation and portable packaging

Estimate resources to catch dimensional mistakes before full data generation.
Treat runtime as a range, not a guarantee.

## Three estimates

1. **Configuration estimate:** before GeoCLEWs, use horizon, timeslices,
   clusters, crop options, expected technologies, and modes.
2. **Structural estimate:** after CLEWs CSV generation, use actual sets, active
   technology-mode pairs, and sparse input/output/emission links.
3. **Post-import estimate:** before full MUIO generation, use imported
   associations, scenario rows, UDCs, and active formulation dimensions.

Run `python scripts/estimate_resources.py` for a transparent structural
estimate. Supplement it with formulation-specific counts when the installed
MUIO generator exposes them.

## Core dimensions

Report at least:

```text
activity combinations
  = regions × years × timeslices × active technology-mode pairs

commodity-balance combinations
  = regions × years × timeslices × commodities

capacity-time combinations
  = regions × years × timeslices × technologies
```

Estimate rows, columns, and nonzeros from the active formulation and sparse
connectivity. Report memory and disk as ranges with declared bytes-per-entry
and safety factors. Estimate solve time only as a broad empirical range.

## Traffic lights

- **Green:** estimated peak memory and working disk are below 50% of available
  resources.
- **Amber:** either is 50–80%, runtime is unusually long, or a dimension is
  substantially larger than comparable builds. Require explicit acknowledgement
  in the build report.
- **Red:** estimated memory or disk exceeds 80%, available disk is insufficient,
  or an unexplained association expansion is present. Stop before generation.

Do not automatically reduce years, timeslices, clusters, technologies, modes,
or spatial coverage. Such reductions change the model architecture and require
an explicit structural decision.

After solving, append actual rows, columns, nonzeros, peak/observed memory when
available, LP size, working-directory size, generation time, and solve time.

## Portable package

Include:

- complete model JSON and configuration;
- generated raw inputs and source configuration;
- final solver status, log, and result exports;
- prepared workbook and otoole configuration;
- import, repair, parity, audit, and reproduction scripts;
- required documentation and diagnostics;
- regression fixtures for applied corrections; and
- version/checksum records.

After all raw checks pass, run `scripts/freeze_raw_baseline.py`. Retain one
source/build archive and the existing portable raw MUIO ZIP. Do not make a
second identical MUIO copy. The source archive excludes portable MUIO ZIPs,
LP/MPS files, caches, its own backups, and its manifest.

Do not archive complete upstream Git checkouts when pinned commits reproduce
them. Do not redistribute restricted datasets. Record exact editions,
retrieval instructions, and checksums for actual input files because code pins
alone do not freeze mutable downloads.

Require `config/baseline_manifest.json` to match both artifacts and the current
raw input/result tree hashes.

Exclude regenerable LP/MPS files from the portable ZIP by default. Document the
command that recreates them. Never exclude authoritative inputs, solver status,
or evidence required to explain the representation.

Run an archive integrity test and `python scripts/validate_delivery.py`. Report
working case size and portable archive size separately.
