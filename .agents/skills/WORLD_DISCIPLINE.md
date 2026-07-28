# World discipline — read this before touching any model

A machine can carry more than one MUIOGO installation, and they must not be
confused with each other:

| World | What it is | Who drives it |
|---|---|---|
| **live** | The user's own checkouts, on their own branches, used for hand work | The user, usually through the web interface |
| **runtime** | A self-contained installation built by MUIOGO-AI's installer | You, headless |

They hold different cases, different scenarios, different results, and different
OG model registries. A run started in one is invisible in the other.

## The rules

**1. Say which world you are in, before you act and again when you report.**

Every `muiogo` command prints its world to stderr as its first line:

```
world: runtime (installed) · http://127.0.0.1:5102 · /Users/x/muiogo-ai/MUIOGO [pinned by launcher]
```

Read it. Put it in what you tell the user. "I ran the carbon tax scenario" is not
a complete sentence here — "I ran it in the runtime world" is. If you are about
to report a number, the user needs to know which installation produced it.

**2. Use the launcher, never bare `muiogo`.**

```bash
muiogo-ai <command>     # the installed runtime — always, regardless of anything else
muiogo-live <command>   # the user's own checkouts — only when they asked for that
```

Each launcher carries its world's manifest path inside it as an absolute
literal, so it cannot be retargeted by an environment variable, a working
directory, or anything you or the user did earlier. Bare `muiogo` resolves from
the search path and can land anywhere; it exists for people, not for you.

If `muiogo-ai` is not on PATH, call it by full path (`~/.local/bin/muiogo-ai`).
Do not fall back to bare `muiogo` — that is how the wrong world gets touched.

**3. Never address a case by a relative path.**

Wrong, and the most common way to cross worlds without noticing:

```bash
python scripts/audit_something.py WebAPP/DataStorage/MyCase
```

That resolves against whatever directory you happen to be in. Ask instead:

```bash
CASE="$(muiogo-ai case-path --case 'MyCase')"
python scripts/audit_something.py "$CASE"
```

`case-path` returns the absolute path inside the current world, and fails loudly
if the case does not exist there — which is the answer you want, rather than
silently operating on a same-named case somewhere else.

**4. Pass the world down to anything you start.**

A launcher exports `MUIOGO_WORLD_FILE` and `MUIOGO_HOME`, and child processes
inherit them. So a script run *from* a launcher-issued command is already in the
right world. A script you run directly is not. Prefer invoking work through
`muiogo-ai`; if you must run a script yourself, run it from a shell that the
launcher started, or pass `--url` explicitly.

**5. Treat a world crossing as a stop, not a warning.**

Exit code **3** means the command refused because a path belonged to a different
world. Do not retry with the guard sidestepped, do not pass `--data-storage` to
force it through, and do not switch worlds to make the error go away. Tell the
user what happened and which two worlds were involved.

**6. Never act on the live world unless the user asked for it.**

The live world holds work the user did by hand, on branches they chose. Results
there are theirs. If a request seems to need it — "run this on my Philippines
model" — say which world you believe they mean and what you are about to touch,
and wait for them to confirm. Do not switch to it because a case was not found
in the runtime world; report that instead.

## When you do not know which world you are in

Ask, cheaply:

```bash
muiogo-ai status          # this world: paths, port, cases, OG models
muiogo worlds             # every world on the machine, with its record
```

`muiogo worlds` is the only command that deliberately looks across worlds. Use
it to orient, never to pick a target: the target comes from the launcher.
