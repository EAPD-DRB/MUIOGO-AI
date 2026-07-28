# MUIOGO on-disk results contract (observed)

What lands where when a case run solves. Observed against MUIOGO @ `3db8b816`
(2026-07-27), CLEWs Demo case, CBC solver. Analysis skills should read these
files (directly or via the download endpoints), never scrape the GUI.

## Layout

```
WebAPP/DataStorage/
├── Parameters.json, Variables.json,        # app-level definitions
│   Duals.json, Indicators.json
└── <case>/                                 # e.g. "CLEWs Demo"
    ├── genData.json                        # case definition (osy-casename, ...)
    ├── R.json, RY*.json, RT*.json, ...     # parameter data by dimension group
    ├── view/                               # saved GUI views
    └── res/
        └── <run>/                          # e.g. REF, CO2TAX (one per scenario run)
            ├── data.txt                    # generated MathProg data (generateDataFile)
            ├── data_processed.txt          # preprocessor output (CBC path)
            ├── lp.lp                       # LP file built by glpsol --check (CBC path)
            ├── results.txt                 # raw solver solution
            └── csv/                        # parsed results, one CSV per variable (32 for demo)
```

## Result CSVs

- One file per OSeMOSYS output variable: `NewCapacity.csv`,
  `AnnualTechnologyEmission.csv`, `Demand.csv`, `RateOfActivity.csv`,
  `TotalCapacityAnnual.csv`, ... (32 for the demo case).
- Long/tidy format. Header = dimension letters + variable name; one row per
  index combination. Examples observed:
  - `NewCapacity.csv`: `r,t,y,NewCapacity` → `RE1,MINCOA,2020,473.04`
  - `AnnualTechnologyEmission.csv`: `r,t,e,y,AnnualTechnologyEmission` →
    `RE1,MINCOA,CO2,2020,24583.04`
- Dimension letters follow OSeMOSYS sets: `r` region, `t` technology, `f` fuel,
  `e` emission, `y` year, `l` timeslice, `m` mode, `s` storage.

## Lifecycle facts that matter to tooling

- `POST /run` deletes the run's previous results before solving; a missing
  `results.txt`/`csv/` after a run means the solve failed even if HTTP was 200.
- `data.txt` regeneration is deterministic: regenerated file was byte-identical
  to the shipped demo one.
- Timestamps on `res/<run>/` files are the reliable "when did this last solve"
  signal.
- Case names may contain spaces ("CLEWs Demo") — always quote/encode paths.

## Stored results can predate the input data (verified 2026-07-28)

Two findings that matter whenever you compare against results you did not
generate:

- **The demo case ships a stale CO2TAX result.** `res/CO2TAX/csv` as shipped
  reports 600,590 tonnes cumulative CO2, but re-solving the same case with the
  shipped input data gives **513,337** (objective 69,679.03), reproducibly and
  identically in both the original case and a fresh copy. REF (730,895) and
  RETRG (707,668) do reproduce. So the stored CO2TAX outputs were produced by
  input data or a MUIOGO version that is no longer what the case contains.
- **A re-solve writes fewer result variables than the shipped runs carry.**
  Untouched shipped runs hold 44 CSVs; runs solved by current MUIOGO hold 32.

Consequence for tooling and skills: **treat stored results as unverified.** If a
comparison matters, re-solve every run in it so all numbers come from the same
input data and the same code. `muiogo compare` reads whatever is on disk and
cannot tell how old it is.
