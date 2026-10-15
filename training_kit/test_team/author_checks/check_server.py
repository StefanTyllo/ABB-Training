"""Author HTTP checks. These do not verify JavaScript or Selenium behavior."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

SERVER = Path(__file__).resolve().parents[1] / "scaffold" / "server.py"


def request(url, data=None):
    payload = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(url, payload, {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


assert SERVER.exists(), "The runnable server has not been implemented"
for index, variant in enumerate(("correct", "no-persist", "bad-boundary")):
    with tempfile.TemporaryDirectory() as directory:
        port = 18820 + index
        process = subprocess.Popen([sys.executable, str(SERVER), "--port", str(port),
                                    "--variant", variant, "--state", directory + "/state.json"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        url = f"http://127.0.0.1:{port}"
        try:
            for _ in range(50):
                try:
                    _, defaults = request(url + "/api/settings")
                    break
                except OSError:
                    time.sleep(.05)
            else:
                raise AssertionError("Server did not become ready")
            changed = {**defaults, "connection": "tcp", "host": "example.test", "port": "1502"}
            assert request(url + "/api/settings", changed)[0] == 200
            assert request(url + "/api/settings")[1] == (defaults if variant == "no-persist" else changed)
            assert request(url + "/api/settings", {**changed, "port": "0"})[0] == 400
            assert request(url + "/api/settings", {**changed, "port": "65536"})[0] == 400
            assert request(url + "/api/settings", {**changed, "port": "65535"})[0] == (400 if variant == "bad-boundary" else 200)
            assert request(url + "/api/reset", {})[1] == defaults
            print(f"HTTP contracts verified: {variant}")
        finally:
            process.terminate()
            process.wait(timeout=5)
