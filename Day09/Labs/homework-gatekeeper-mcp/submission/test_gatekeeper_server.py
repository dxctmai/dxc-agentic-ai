from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SERVER = ROOT / "gatekeeper_server.py"


def run_case(label: str, command: list[str], expected: str) -> None:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=20, cwd=ROOT)
        output = (completed.stdout or "") + (completed.stderr or "")
        if expected in output:
            print(f"PASS {label}")
        else:
            print(f"FAIL {label}")
            print(output.strip())
    except Exception as exc:
        print(f"FAIL {label}")
        print(str(exc))


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Path(tmpdir) / "mcp.json"
        config.write_text(
            json.dumps(
                {
                    "servers": {
                        "gatekeeper": {
                            "command": sys.executable,
                            "args": [str(SERVER)],
                            "cwd": str(ROOT),
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

        list_command = [sys.executable, str(SERVER), "--http"]
        server = subprocess.Popen(list_command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            time.sleep(2)
            run_case("list tools", [sys.executable, str(SERVER)], "AskIT Gatekeeper")
            run_case("route_ticket 1", [sys.executable, str(SERVER)], "Security")
            run_case("route_ticket 2", [sys.executable, str(SERVER)], "Access")
            run_case("route_ticket 3", [sys.executable, str(SERVER)], "General")
            run_case("needs_approval 1", [sys.executable, str(SERVER)], "False")
            run_case("needs_approval 2", [sys.executable, str(SERVER)], "True")
            run_case("needs_approval 3", [sys.executable, str(SERVER)], "True")
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()


if __name__ == "__main__":
    main()