# muiogo-client

Thin Python client and `muiogo` CLI for the MUIOGO HTTP API. Mechanical work
only — session handling, case CRUD, run launch, results download. No analysis,
no judgment: that lives in the skills.

Verified end-to-end against MUIOGO @ `3db8b816` (the pin): list cases, copy the
demo case, generate a data file, solve with CBC (optimal), download all 32
result CSVs, delete the copy. See `../docs/API_ENDPOINTS.md` for the endpoint
reference this encodes.

## Use

```bash
uv sync          # in this directory
uv run muiogo serve --root /path/to/MUIOGO      # headless server (foreground)
uv run muiogo cases
uv run muiogo run --case "CLEWs Demo" --run REF --solver cbc
uv run muiogo results --case "CLEWs Demo" --run REF --out ./ref-results
```

Python:

```python
from muiogo_client import MuiogoClient, MuiogoServer

server = MuiogoServer("/path/to/MUIOGO").start()
client = MuiogoClient()
client.run("CLEWs Demo", "REF")            # generates data file + solves (CBC)
client.download_all_csvs("CLEWs Demo", "REF", "out/")
server.stop()
```

Notes: `/run` is synchronous and returns HTTP 200 even on solver failure — the
client raises `MuiogoError` when the body's `status_code` is `"error"`. The
`glpk` solver option is broken upstream at the pin (no preprocessing); use
`cbc` until the upstream fix lands. Solvers must be installed
(`brew install glpk cbc` on macOS).
