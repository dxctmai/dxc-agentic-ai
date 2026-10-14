from __future__ import annotations

import argparse

from fastmcp import FastMCP

from gatekeeper import needs_approval as gatekeeper_needs_approval
from gatekeeper import route as gatekeeper_route


mcp = FastMCP("AskIT Gatekeeper")


@mcp.tool(description="Route a ticket text to the most likely support team.")
def route_ticket(text: str) -> str:
    return gatekeeper_route(text)


@mcp.tool(description="Check whether an action needs approval for a user at a given hour.")
def needs_approval(action: str, user_id: str, hour: int) -> bool:
    result = gatekeeper_needs_approval(action, user_id, hour)
    return bool(result["approval"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="Run the server over HTTP on port 8778.")
    args = parser.parse_args()

    if args.http:
        mcp.run(transport="http", host="127.0.0.1", port=8778)
    else:
        mcp.run()


if __name__ == "__main__":
    main()