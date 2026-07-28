# MUIOGO-AI

Run [MUIOGO](https://github.com/EAPD-DRB/MUIOGO) — the UN DESA modelling
interface for CLEWs and OG-Core — without the GUI, driven by AI skills:
install it, run scenarios, couple it with OG country models, and get
analytical outputs on demand.

Works on macOS and Linux. Windows is not supported yet.

## Requirements

Git. If you don't have it:

macOS:

```bash
xcode-select --install
```

Linux (Debian/Ubuntu):

```bash
sudo apt install git
```

## Install (about 15 minutes)

Open a terminal (macOS: press Cmd+Space, type `Terminal`, press Enter) and
run:

```bash
git clone https://github.com/EAPD-DRB/MUIOGO-AI.git
```

```bash
cd MUIOGO-AI
```

```bash
./scripts/install.sh --country PHL
```

This installs MUIOGO, the Philippines example country, and the OG-CLEWS
link, and checks that everything works before finishing.

At the end it offers to install the modelling skills for use outside this
repository. You can say no and do it later — see below.

## The AI skills

The skills teach an AI assistant how to build, calibrate, run, and review these
models. **Inside this repository there is nothing to install** — open it in
Claude Code or Codex (`cd MUIOGO-AI`, then `claude` or `codex`) and the skills
are already active. Ask for what you want in plain language, for example
*"assess the calibration of this CLEWs model"* or *"run the preflight checks
before I start this solve"*.

New to this? [docs/USING_THE_SKILLS.md](docs/USING_THE_SKILLS.md) walks through
three worked examples with the exact prompts to type.

To use them in your own model repositories too:

```bash
./scripts/install-skills.sh
```

It asks which assistant you use (Claude Code, Codex, both, or a folder you
name) and copies the skills there; restart your assistant afterwards.

See [SKILLS.md](SKILLS.md) for the full list and what each one does.

## Start MUIOGO

```bash
muiogo-ai serve --detach
```

Leave that window open. For the web interface, open
[http://127.0.0.1:5102](http://127.0.0.1:5102) in your browser. Press
Ctrl+C in the terminal to stop.

## If something goes wrong

- **"port … is already in use"** — add `--port 5103` to the command. (The installed runtime uses 5102; 5002 is left for a MUIOGO you run yourself.)
- **A message about conda** — run `conda deactivate` and try again.
- Still stuck? The installer writes logs into `~/muiogo-ai/` —
  share the newest `.log` file when asking for help.

## Manual installation

The installer above just runs each project's own installer for you. To do it
by hand instead:

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

- Layout: `docs/` (scope and design), `.agents/skills/` (the skills;
  `.claude/skills/` holds one symlink each), [SKILLS.md](SKILLS.md) (the
  catalogue), `client/` (Python client + `muiogo` CLI), `clews/` (country
  catalog), `experiments/` (studies).
- Start with [docs/SCOPE.md](docs/SCOPE.md); install details are in
  [docs/INSTALL_DESIGN.md](docs/INSTALL_DESIGN.md).
- One hard rule: talk to MUIOGO over HTTP only — never import its backend
  code. Process is light: push to `main`, branch when you want review.

## License

Apache License 2.0 (`LICENSE`), same as MUIOGO.
