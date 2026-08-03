# World discipline — read this before touching any model

A machine can carry two separate MUIOGO setups, and they must not be confused
with each other:

| Setup | What it is | Who drives it | How it is found |
|---|---|---|---|
| **the installation** | A self-contained muiogoai built by the installer | You, headless | Only through the `muiogo-ai` launcher — no registry, no pointer |
| **adopted** | The user's own checkouts, on their own branches, used for hand work | The user, usually through the web interface | The single manifest `muiogo adopt` writes |

They hold different cases, different scenarios, different results, and
different OG model registries. A run started in one is invisible in the other.
There is no machine-wide list of setups and no switching command: which setup a
command acts on is decided by which command you ran, before any code executes.

## The rules

**1. Say which setup you are in, before you act and again when you report.**

Every command prints its setup to stderr as its first line:

```
world: muiogoai (installed) · http://127.0.0.1:5102 · /Users/x/muiogoai/MUIOGO [pinned by launcher]
```

Read it. Put it in what you tell the user. "I ran the carbon tax scenario" is
not a complete sentence here — say which installation produced the number.

**2. Use the launcher, never bare `muiogo`.**

```bash
muiogo-ai <command>     # the installation — always, regardless of anything else
muiogo-live <command>   # the user's own checkouts — only when they asked for that
```

Each launcher carries its setup's manifest path inside it as an absolute
literal, so it cannot be retargeted by an environment variable, a working
directory, or anything you or the user did earlier. Bare `muiogo` resolves the
adopted manifest and exists for people, not for you — and it cannot see the
installation at all, by design.

If `muiogo-ai` is not on PATH, call it by full path (`~/.local/bin/muiogo-ai`).
Do not fall back to bare `muiogo` — that is how the wrong setup gets touched.

**3. Never address a case by a relative path.**

Wrong, and the most common way to cross setups without noticing:

```bash
python scripts/audit_something.py WebAPP/DataStorage/MyCase
```

That resolves against whatever directory you happen to be in. Ask instead:

```bash
CASE="$(muiogo-ai case-path --case 'MyCase')"
python scripts/audit_something.py "$CASE"
```

`case-path` returns the absolute path inside the current setup, and fails
loudly if the case does not exist there — which is the answer you want, rather
than silently operating on a same-named case somewhere else.

**4. Pass the setup down to anything you start.**

A launcher exports `MUIOGO_WORLD_FILE` and `MUIOGO_HOME`, and child processes
inherit them. So a script run *from* a launcher-issued command is already in
the right setup. A script you run directly is not. Prefer invoking work through
`muiogo-ai`; if you must run a script yourself, run it from a shell that the
launcher started, or pass `--url` explicitly.

**5. Treat a crossing as a stop, not a warning.**

Exit code **3** means the command refused because a path belonged to the other
setup. Do not retry with the guard sidestepped, do not pass `--data-storage` to
force it through. Tell the user what happened and which two setups were
involved. One asymmetry to know: a `muiogo-ai` command can detect a path inside
the adopted checkouts, but bare `muiogo` cannot detect a path inside the
installation — it does not know one exists. That is not a loophole to use; it
is one more reason everything you do goes through `muiogo-ai`.

**6. Never act on the adopted setup unless the user asked for it.**

The adopted checkouts hold work the user did by hand, on branches they chose.
Results there are theirs. If a request seems to need it — "run this on my
Philippines model" — say which setup you believe they mean and what you are
about to touch, and wait for them to confirm. Do not switch because a case was
not found in the installation; report that instead.

## When you do not know where you are

Ask, cheaply — one command per setup, no cross-listing exists:

```bash
muiogo-ai status          # the installation: paths, port, cases, OG models
muiogo status             # the user's own checkouts, if any are adopted
```
