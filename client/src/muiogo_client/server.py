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
        py = self.root / ".venv" / "bin" / "python"
        if not py.exists():
            raise ServerError(
                f"No venv python at {py}. Run 'uv sync' in {self.root} first."
            )
        return py

    def _og_env(self):
        """OG model/state locations from the installed manifest.

        MUIOGO resolves its OG calibration registry from MUIOGO_OG_MODELS_DIR and
        MUIOGO_OG_DATA_DIR, defaulting to ~/.muiogo. A workspace installed
        elsewhere would otherwise have its registered country models invisible to
        the server we start.
        """
        try:
            from muiogo_client import workspace
            data, _ = workspace.load()
        except Exception:
            return {}
        env = {}
        muiogo = data.get("muiogo") or {}
        if muiogo.get("og_models_dir"):
            env["MUIOGO_OG_MODELS_DIR"] = muiogo["og_models_dir"]
        if muiogo.get("og_state_dir"):
            env["MUIOGO_OG_DATA_DIR"] = muiogo["og_state_dir"]
        return env

    def start(self, wait_seconds=30):
        """Spawn the server headless and wait until it answers."""
        if self.is_running():
            return self
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
        d = Path.home() / ".muiogo" / "servers"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def pidfile(self):
        """Where a detached server records its process id.

        Recorded per port so stopping is exact. Killing by port — e.g.
        `kill $(lsof -ti :5002)` — can match an unrelated process that happens to
        hold the port, which is a real hazard in a headless setting.
        """
        return self._state_dir() / f"port-{self.port}.pid"

    def start_detached(self, wait_seconds=60, log_path=None):
        """Start headless in the background and record the pid. Returns the pid."""
        if self.is_running():
            raise ServerError(f"something is already answering on {self.url}")
        app = self.root / "API" / "app.py"
        if not app.exists():
            raise ServerError(f"Not a MUIOGO checkout: {app} missing.")
        log = Path(log_path) if log_path else (self._state_dir() / f"port-{self.port}.log")
        log.parent.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, PORT=str(self.port), **self._og_env())
        with open(log, "ab") as handle:
            proc = subprocess.Popen(
                [str(self._python()), str(app)], cwd=str(self.root), env=env,
                stdout=handle, stderr=handle, start_new_session=True)
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
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            path.unlink(missing_ok=True)
            return None
        for _ in range(20):
            if not self.is_running():
                break
            time.sleep(0.5)
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
