"""Start and stop a headless MUIOGO server.

MUIOGO's own start.sh force-opens a browser; running `<root>/.venv/bin/python
API/app.py` directly does not (verified against 3db8b816). This wraps exactly
that, plus a readiness poll on /getSession.
"""
import os
import signal
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path


class ServerError(RuntimeError):
    pass


class MuiogoServer:
    def __init__(self, root, port=5002):
        self.root = Path(root)
        self.port = int(port)
        self.url = f"http://127.0.0.1:{self.port}"
        self.process = None

    def _python(self):
        """The checkout's own interpreter, on either platform.

        Uses the same resolver as everything else — POSIX puts it at
        .venv/bin/python, Windows at .venv/Scripts/python.exe. Hardcoding the
        POSIX path here made serve and stop impossible on Windows.
        """
        from muiogo_client.workspace import venv_python
        py = venv_python(self.root)
        if py is None:
            raise ServerError(
                f"No virtual environment in {self.root}. Run 'uv sync' there first."
            )
        return py

    def _og_env(self):
        """OG registry variables for the checkout at self.root.

        These MUST come from the world that owns this root. Reading them from
        the active world instead meant that starting the installed runtime's
        server while the pointer said "live" injected the live world's registry
        into it — and because MUIOGO's Config.py reads os.environ before its own
        .env, the injected value won. The runtime then wrote its OG
        registrations straight into the user's manual registry, which is the one
        failure the installer treats as fatal.
        """
        from muiogo_client.workspace import world_for_root
        world = world_for_root(self.root)
        if world is None:
            # No record for this checkout: say nothing rather than inject a
            # guess. MUIOGO then reads its own .env, which is the right answer.
            return {}
        return {"MUIOGO_OG_MODELS_DIR": str(world.og_models_dir),
                "MUIOGO_OG_DATA_DIR": str(world.og_state_dir)}

    def start(self, wait_seconds=30):
        """Spawn the server headless and wait until it answers."""
        if self.is_running():
            # Something already answers here, and HTTP gives us no way to ask it
            # which checkout it is serving. Treating it as ours is how a run
            # aimed at the installed world silently lands in the live one, so
            # say so instead of assuming.
            raise ServerError(
                f"something is already answering on {self.url}; refusing to assume "
                f"it is serving {self.root}. Stop it, or choose another port.")
        app = self.root / "API" / "app.py"
        if not app.exists():
            raise ServerError(f"Not a MUIOGO checkout: {app} missing.")
        env = dict(os.environ, PORT=str(self.port), **self._og_env())
        self.process = subprocess.Popen(
            [str(self._python()), str(app)],
            cwd=str(self.root),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            if self.is_running():
                return self
            if self.process.poll() is not None:
                raise ServerError(
                    f"Server exited immediately (code {self.process.returncode}). "
                    f"Run '{self._python()} API/app.py' in {self.root} to see why."
                )
            time.sleep(0.5)
        raise ServerError(f"Server did not answer on {self.url} within {wait_seconds}s.")

    def is_running(self):
        try:
            with urllib.request.urlopen(f"{self.url}/getSession", timeout=2):
                return True
        except (urllib.error.URLError, OSError):
            return False

    def _state_dir(self):
        """Where server run-state lives: never inside a model checkout.

        An adopted world points at repos someone uses for live work, so writing a
        pidfile or log there would leave untracked files in their repository.
        """
        from muiogo_client.workspace import servers_dir
        d = servers_dir()
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _tag(self):
        """A filename-safe identity for this checkout.

        Keying run-state on the port alone meant two worlds on the same port
        shared one pidfile: `stop` in one killed the other's server, and
        starting the second overwrote the first's recorded pid.
        """
        import hashlib
        real = str(Path(self.root).resolve())
        return hashlib.sha256(real.encode()).hexdigest()[:10]

    def pidfile(self):
        """Where a detached server records its process id.

        Recorded per port so stopping is exact. Killing by port — e.g.
        `kill $(lsof -ti :5002)` — can match an unrelated process that happens to
        hold the port, which is a real hazard in a headless setting.
        """
        return self._state_dir() / f"{self._tag()}-{self.port}.pid"

    def start_detached(self, wait_seconds=60, log_path=None):
        """Start headless in the background and record the pid. Returns the pid."""
        if self.is_running():
            raise ServerError(f"something is already answering on {self.url}")
        app = self.root / "API" / "app.py"
        if not app.exists():
            raise ServerError(f"Not a MUIOGO checkout: {app} missing.")
        log = Path(log_path) if log_path else (self._state_dir() / f"{self._tag()}-{self.port}.log")
        log.parent.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, PORT=str(self.port), **self._og_env())
        # Detach so the server outlives this process. setsid is POSIX; Windows
        # wants a new process group instead.
        spawn = {}
        if os.name == "nt":
            spawn["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        else:
            spawn["start_new_session"] = True
        with open(log, "ab") as handle:
            proc = subprocess.Popen(
                [str(self._python()), str(app)], cwd=str(self.root), env=env,
                stdout=handle, stderr=handle, **spawn)
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            if self.is_running():
                self.pidfile().write_text(f"{proc.pid}\n", encoding="utf-8")
                self.process = proc
                return proc.pid
            if proc.poll() is not None:
                raise ServerError(f"server exited immediately (code {proc.returncode}); "
                                  f"see {log}")
            time.sleep(0.5)
        proc.terminate()
        raise ServerError(f"server did not answer on {self.url} within {wait_seconds}s; "
                          f"see {log}")

    def stop_detached(self):
        """Stop the server recorded in the pidfile. Returns the pid, or None."""
        path = self.pidfile()
        if not path.is_file():
            return None
        try:
            pid = int(path.read_text().strip())
        except (OSError, ValueError):
            path.unlink(missing_ok=True)
            return None
        # os.kill on Windows ignores the signal and terminates abruptly whatever
        # you pass, so ask for a graceful stop only where that means something.
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                               capture_output=True, timeout=30)
            else:
                os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, OSError, subprocess.SubprocessError):
            path.unlink(missing_ok=True)
            return None
        for _ in range(20):
            if not self.is_running():
                break
            time.sleep(0.5)
        if self.is_running() and os.name != "nt":
            try:
                os.kill(pid, signal.SIGKILL)      # it ignored the polite request
            except (ProcessLookupError, OSError):
                pass
            for _ in range(10):
                if not self.is_running():
                    break
                time.sleep(0.5)
        if self.is_running():
            # Deleting the pidfile now would throw away the only record of what
            # is holding the port, leaving a server nothing can stop by name.
            raise ServerError(
                f"pid {pid} is still answering on {self.url} after SIGTERM and "
                f"SIGKILL. Its pid is kept in {path} — investigate before retrying.")
        path.unlink(missing_ok=True)
        return pid

    def stop(self):
        """Stop the server if this object started it."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None
