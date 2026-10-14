from __future__ import annotations

import subprocess
import sys
import asyncio
from pathlib import Path

from fastmcp.client import Client, PythonStdioTransport


ROOT = Path(__file__).resolve().parent
SERVER = ROOT / "gatekeeper_server.py"


def main() -> None:
    asyncio.run(main_async())


async def main_async() -> None:
    transport = PythonStdioTransport(script_path=SERVER, cwd=str(ROOT), python_cmd=sys.executable)
    async with Client(transport) as client:
        tools = await client.list_tools()
        tool_names = {tool.name for tool in tools}
        print("PASS list tools" if {"route_ticket", "needs_approval"}.issubset(tool_names) else "FAIL list tools")

        route_examples = [
            ("route_ticket 1", {"text": "phishing email reported"}, "Security"),
            ("route_ticket 2", {"text": "wifi and vpn are down"}, "Network"),
            ("route_ticket 3", {"text": "new laptop keyboard broken"}, "Hardware"),
        ]
        for label, args, expected in route_examples:
            result = await client.call_tool("route_ticket", args)
            print(f"PASS {label}" if expected in str(result) else f"FAIL {label}")

        approval_examples = [
            ("needs_approval 1", {"action": "search_kb", "user_id": "EMP-9999", "hour": 10}, "False"),
            ("needs_approval 2", {"action": "grant_access", "user_id": "EMP-1001", "hour": 10}, "True"),
            ("needs_approval 3", {"action": "update_ticket", "user_id": "EMP-9999", "hour": 21}, "True"),
        ]
        for label, args, expected in approval_examples:
            result = await client.call_tool("needs_approval", args)
            print(f"PASS {label}" if expected in str(result) else f"FAIL {label}")


if __name__ == "__main__":
    main()