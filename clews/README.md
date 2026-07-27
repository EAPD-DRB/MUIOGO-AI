# CLEWs country catalog and manifests

The CLEWs side of country installation, mirroring how OG models solve it.

- `clews-repos.json` — the catalog: which repos ship portable MUIO cases
  (the CLEWs analogue of the OG installer's `repos.json`).
- `countries/<ISO3>.json` — one manifest per country: its cases (with roles
  and a recommended default), where the archives live, checksums, and its OG
  counterpart. These are **overlay manifests**: the spec is designed to live
  inside each CLEWs country repo as `clews-country.json` (self-describing data
  packages), and is hosted here only until that migration is proposed
  upstream. When a country repo carries its own manifest, the in-repo copy
  wins.

**Matching**: ISO3 is the join key everywhere. The OG installer derives
`PHL` from `OG-PHL`; a CLEWs manifest declares `iso3: PHL`; the composed
installer's `--country PHL` resolves both sides plus link registration from
that one key. Nobody maintains a central mapping table.

Used by `scripts/install.sh` (`--clews`, `--country`, `--case`). Cases are
installed into MUIOGO headless through its own `/uploadCase` HTTP endpoint —
the same validated path the GUI's restore uses.
