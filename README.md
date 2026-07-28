# MUIOGO-AI

Run [MUIOGO](https://github.com/EAPD-DRB/MUIOGO) — the UN DESA modelling
interface for CLEWs and OG-Core — without the GUI, driven by AI skills:
install it, run scenarios, couple it with OG country models, and get
analytical outputs on demand.

Works on macOS and Linux. Windows is not supported yet.

## Install (about 15 minutes)

**1. Open a terminal** (macOS: press Cmd+Space, type `Terminal`, press Enter).

**2. Install Git** (skip if you have it):

macOS:

```bash
xcode-select --install
```

Linux (Debian/Ubuntu):

```bash
sudo apt install git gh
```

**3. Sign in to GitHub** (needed while this project is private; on macOS
install the GitHub tool first with `brew install gh` — if `brew` is missing,
get it at [brew.sh](https://brew.sh)):

```bash
gh auth login
```

Press Enter to accept the defaults and sign in through your browser.

**4. Go to your projects folder and download MUIOGO-AI:**

```bash
cd ~
gh repo clone EAPD-DRB/MUIOGO-AI
cd MUIOGO-AI
```

**5. Install everything** (MUIOGO, the Philippines example country, and the
OG-CLEWS link — the script checks that it all works before finishing):

```bash
./scripts/install.sh --country PHL
```

**6. Start MUIOGO:**

```bash
client/.venv/bin/muiogo serve --root ~/muiogo-ai-workspace/MUIOGO
```

Leave that window open. To use the web interface, open
[http://127.0.0.1:5002](http://127.0.0.1:5002) in your browser. Press
Ctrl+C in the terminal to stop.

## If something goes wrong

- **"port 5002 is already in use"** — add `--port 5003` to the command.
- **A message about conda** — run `conda deactivate` and try again.
- **"could not clone"** — step 3 (GitHub sign-in) didn't finish; run
  `gh auth login` again.
- Still stuck? The installer writes logs into `~/muiogo-ai-workspace/` —
  share the newest `.log` file when asking for help.

## Manual installation

The one-line installer above just runs each project's own installer for you.
To do it by hand instead:

1. **MUIOGO** — follow the install instructions in the
   [MUIOGO README](https://github.com/EAPD-DRB/MUIOGO#installation).
2. **An OG country model** — use the OG-Core universal installer:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/PSLmodels/OG-Core/master/scripts/install.sh -o og-install.sh
   bash og-install.sh --repo og-phl --dest ~/.muiogo/og-models --yes
   ```

3. **ogclews-link** — clone it and run its setup:

   ```bash
   git clone https://github.com/marcelolafleur/ogclews-link.git
   cd ogclews-link && ./scripts/setup.sh --og-path ~/.muiogo/og-models/OG-PHL
   ```

## For contributors

- Layout: `docs/` (scope and design), `.claude/skills/` (the agent skills),
  `client/` (Python client + `muiogo` CLI), `clews/` (country catalog),
  `experiments/` (studies).
- Start with [docs/SCOPE.md](docs/SCOPE.md); install details are in
  [docs/INSTALL_DESIGN.md](docs/INSTALL_DESIGN.md).
- One hard rule: talk to MUIOGO over HTTP only — never import its backend
  code. Process is light: push to `main`, branch when you want review.

## License

Apache License 2.0 (`LICENSE`), same as MUIOGO.
