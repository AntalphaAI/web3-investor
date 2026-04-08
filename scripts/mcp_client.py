#!/usr/bin/env python3
"""
Web3 Investor MCP Client

Wrapper that calls the MCP server at https://mcp-skills.ai.antalpha.com/mcp
All logic runs on the remote server.

Usage:
    python3 scripts/mcp_client.py discover --chain ethereum --min-apy 5
    python3 scripts/mcp_client.py analyze --product-id aave-usdc-base --depth detailed
    python3 scripts/mcp_client.py compare --ids aave-usdc-base compound-usdc-ethereum
    python3 scripts/mcp_client.py feedback --product-id aave-usdc-base --feedback helpful
    python3 scripts/mcp_client.py confirm-intent --session-id xxx --type stablecoin --risk moderate
    python3 scripts/mcp_client.py get-intent --session-id xxx
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from typing import Any, Optional

MCP_SERVER_URL = "https://mcp-skills.ai.antalpha.com/mcp"


def call_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Call an MCP tool and return the result.
    JSON-RPC 2.0 format for MCP tool calls.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
        "id": 1,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            MCP_SERVER_URL, data=data, headers=headers, method="POST"
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            response_text = response.read().decode("utf-8")
            result = json.loads(response_text)

            if "error" in result:
                return {"error": result["error"]}

            return result.get("result", {})
    except urllib.error.URLError as e:
        return {"error": f"Connection error: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse response: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def discover(
    chain: str,
    min_apy: float = 0,
    max_apy: Optional[float] = None,
    stablecoin_only: bool = False,
    limit: int = 5,
    session_id: Optional[str] = None,
    natural_language: Optional[str] = None,
) -> dict[str, Any]:
    """Discover DeFi investment opportunities (investor_discover)."""
    args: dict[str, Any] = {
        "limit": limit,
    }
    if session_id:
        args["session_id"] = session_id
    if natural_language:
        args["natural_language"] = natural_language
    if max_apy is not None:
        args["structured_preferences"] = {
            "chain": chain,
            "min_apy": min_apy,
            "max_apy": max_apy,
            "asset_type": "stablecoin" if stablecoin_only else "any",
        }
    else:
        args["structured_preferences"] = {
            "chain": chain,
            "min_apy": min_apy,
            "asset_type": "stablecoin" if stablecoin_only else "any",
        }

    return call_mcp_tool("investor_discover", args)


def analyze(
    product_id: str,
    depth: str = "detailed",
    include_history: bool = True,
) -> dict[str, Any]:
    """Deep analysis of a specific opportunity (investor_analyze)."""
    return call_mcp_tool(
        "investor_analyze",
        {
            "product_id": product_id,
            "analysis_depth": depth,
            "include_history": include_history,
        },
    )


def compare(product_ids: list[str]) -> dict[str, Any]:
    """Compare multiple opportunities (investor_compare)."""
    return call_mcp_tool(
        "investor_compare",
        {
            "product_ids": product_ids,
        },
    )


def feedback(
    product_id: str,
    feedback_type: str,
    reason: Optional[str] = None,
) -> dict[str, Any]:
    """Submit feedback on a recommendation (investor_feedback)."""
    args: dict[str, Any] = {
        "product_id": product_id,
        "feedback": feedback_type,
    }
    if reason:
        args["reason"] = reason

    return call_mcp_tool("investor_feedback", args)


def confirm_intent(
    session_id: str,
    intent_type: str,
    risk_profile: str,
    capital_nature: Optional[str] = None,
    liquidity_need: Optional[str] = None,
) -> dict[str, Any]:
    """Confirm user intent after clarification (investor_confirm_intent)."""
    confirmed_intent: dict[str, Any] = {
        "type": intent_type,
        "risk_profile": risk_profile,
    }
    if capital_nature:
        confirmed_intent["capital_nature"] = capital_nature
    if liquidity_need:
        confirmed_intent["liquidity_need"] = liquidity_need

    return call_mcp_tool(
        "investor_confirm_intent",
        {
            "session_id": session_id,
            "confirmed_intent": confirmed_intent,
        },
    )


def get_stored_intent(session_id: str) -> dict[str, Any]:
    """Get stored intent for a session (investor_get_stored_intent)."""
    return call_mcp_tool(
        "investor_get_stored_intent",
        {"session_id": session_id},
    )


def main():
    parser = argparse.ArgumentParser(description="Web3 Investor MCP Client")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    discover_parser = subparsers.add_parser("discover", help="Discover opportunities")
    discover_parser.add_argument(
        "--chain", required=True, help="Blockchain: ethereum, base, arbitrum, optimism"
    )
    discover_parser.add_argument(
        "--min-apy", type=float, default=0, help="Minimum APY percentage"
    )
    discover_parser.add_argument("--max-apy", type=float, help="Maximum APY percentage")
    discover_parser.add_argument(
        "--stablecoin-only", action="store_true", help="Only stablecoin pools"
    )
    discover_parser.add_argument(
        "--limit", type=int, default=5, help="Max results (1-10)"
    )
    discover_parser.add_argument("--session-id", help="Session ID for stored intent")
    discover_parser.add_argument("--natural-language", help="Natural language query")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze opportunity")
    analyze_parser.add_argument(
        "--product-id", required=True, help="Product ID to analyze"
    )
    analyze_parser.add_argument(
        "--depth", choices=["basic", "detailed", "full"], default="detailed"
    )
    analyze_parser.add_argument(
        "--no-history", action="store_true", help="Exclude historical data"
    )

    compare_parser = subparsers.add_parser("compare", help="Compare opportunities")
    compare_parser.add_argument("--ids", nargs="+", required=True, help="Product IDs")

    feedback_parser = subparsers.add_parser("feedback", help="Submit feedback")
    feedback_parser.add_argument("--product-id", required=True, help="Product ID")
    feedback_parser.add_argument(
        "--feedback",
        choices=["helpful", "not_helpful", "invested", "dismissed"],
        required=True,
        help="Feedback type",
    )
    feedback_parser.add_argument("--reason", help="Optional reason")

    confirm_parser = subparsers.add_parser("confirm-intent", help="Confirm intent")
    confirm_parser.add_argument("--session-id", required=True, help="Session ID")
    confirm_parser.add_argument("--type", required=True, help="Intent type")
    confirm_parser.add_argument("--risk", required=True, help="Risk profile")
    confirm_parser.add_argument("--capital-nature", help="Capital nature")
    confirm_parser.add_argument("--liquidity-need", help="Liquidity need")

    get_intent_parser = subparsers.add_parser("get-intent", help="Get stored intent")
    get_intent_parser.add_argument("--session-id", required=True, help="Session ID")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    result = None

    if args.command == "discover":
        result = discover(
            chain=args.chain,
            min_apy=args.min_apy,
            max_apy=args.max_apy,
            stablecoin_only=args.stablecoin_only,
            limit=args.limit,
            session_id=args.session_id,
            natural_language=args.natural_language,
        )
    elif args.command == "analyze":
        result = analyze(
            product_id=args.product_id,
            depth=args.depth,
            include_history=not args.no_history,
        )
    elif args.command == "compare":
        result = compare(product_ids=args.ids)
    elif args.command == "feedback":
        result = feedback(
            product_id=args.product_id,
            feedback_type=args.feedback,
            reason=args.reason,
        )
    elif args.command == "confirm-intent":
        result = confirm_intent(
            session_id=args.session_id,
            intent_type=args.type,
            risk_profile=args.risk,
            capital_nature=args.capital_nature,
            liquidity_need=args.liquidity_need,
        )
    elif args.command == "get-intent":
        result = get_stored_intent(session_id=args.session_id)

    if result:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({"error": "Unknown command"}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
