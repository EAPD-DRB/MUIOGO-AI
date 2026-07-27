"""Start and stop a headless MUIOGO server.

MUIOGO's own start.sh force-opens a browser; running `<root>/.venv/bin/python
API/app.py` directly does not (verified against 3db8b816). This wraps exactly
that, plus a readiness poll on /getSession.
"""
import os
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

    def start(self, wait_seconds=30):
        """Spawn the server headless and wait until it answers."""
        if self.is_running():
            return self
        app = self.root / "API" / "app.py"
        if not app.exists():
            raise ServerError(f"Not a MUIOGO checkout: {app} missing.")
        env = dict(os.environ, PORT=str(self.port))
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

    def stop(self):
        """Stop the server if this object started it."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None
