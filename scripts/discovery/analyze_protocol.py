#!/usr/bin/env python3
"""
Analyze a specific protocol for investment suitability.

Usage:
    python analyze_protocol.py --protocol aave-v3
    python analyze_protocol.py --protocol uniswap --output json
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional

DEFILLAMA_PROTOCOLS = "https://api.llama.fi/protocols"
DEFILLAMA_PROTOCOL = "https://api.llama.fi/protocol/{slug}"


def fetch_protocol(slug: str) -> Optional[dict]:
    """Fetch protocol data from DefiLlama with retry and validation."""
    url = DEFILLAMA_PROTOCOL.format(slug=slug.lower())
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())
            # Validate response structure
            if not isinstance(data, dict):
                print(f"Error: Invalid response format for {slug}", file=sys.stderr)
                return None
            return data
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Error: Protocol '{slug}' not found on DefiLlama", file=sys.stderr)
        else:
            print(f"Error fetching protocol (HTTP {e.code}): {e.reason}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"Error fetching protocol: {e.reason}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON response for {slug}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error fetching protocol: {e}", file=sys.stderr)
        return None


def fetch_all_protocols() -> list:
    """Fetch all protocols list."""
    try:
        with urllib.request.urlopen(DEFILLAMA_PROTOCOLS, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        print(f"Error fetching protocols list: {e}", file=sys.stderr)
        return []


def find_protocol_slug(name: str) -> Optional[str]:
    """Find protocol slug by name with smart matching."""
    protocols = fetch_all_protocols()
    name_lower = name.lower()
    
    # First try exact match
    for p in protocols:
        slug = p.get("slug", "")
        if slug.lower() == name_lower:
            return slug
    
    # Then try name match
    for p in protocols:
        if name_lower in p.get("name", "").lower():
            return p.get("slug") or p.get("name", "").lower().replace(" ", "-")
        if name_lower in p.get("slug", "").lower():
            return p.get("slug")
    
    # For common protocols, suggest correct slug
    common_mappings = {
        "aave": "aave-v3",
        "uniswap": "uniswap-v3",
        "compound": "compound-v3",
    }
    if name_lower in common_mappings:
        print(f"Note: Using '{common_mappings[name_lower]}' instead of '{name}'", file=sys.stderr)
        return common_mappings[name_lower]
    
    return None


def calculate_risk_score(protocol: dict, total_tvl: float = 0) -> dict:
    """Calculate detailed risk score with robust data handling."""
    scores = {}
    total = 0
    
    # Helper to safely get numeric value
    def safe_numeric(value, default=0):
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return default
        return default
    
    # Helper to safely get list length
    def safe_list_len(value):
        if isinstance(value, list):
            return len(value)
        return 0
    
    # Maturity (0-3)
    audits_raw = protocol.get("audits", [])
    if isinstance(audits_raw, list):
        audit_count = len(audits_raw)
    elif isinstance(audits_raw, str):
        # Handle case where audits is a number string like "2"
        try:
            audit_count = int(audits_raw)
        except ValueError:
            audit_count = 0
    else:
        audit_count = 0
        
    if audit_count >= 2:
        scores["maturity"] = {"score": 0, "note": "Multiple audits, well established"}
    elif audit_count == 1:
        scores["maturity"] = {"score": 1, "note": "Single audit"}
    elif protocol.get("audit_note"):
        scores["maturity"] = {"score": 2, "note": "Audit in progress or partial"}
    else:
        scores["maturity"] = {"score": 3, "note": "No audit"}
    total += scores["maturity"]["score"]
    
    # TVL (0-2) - use passed total_tvl
    tvl = safe_numeric(total_tvl, 0)
    if tvl > 1_000_000_000:
        scores["tvl"] = {"score": 0, "note": f"TVL > $1B (${tvl:,.0f})"}
    elif tvl > 100_000_000:
        scores["tvl"] = {"score": 1, "note": f"TVL $100M-$1B (${tvl:,.0f})"}
    else:
        scores["tvl"] = {"score": 2, "note": f"TVL < $100M (${tvl:,.0f})"}
    total += scores["tvl"]["score"]
    
    # Decentralization (0-2)
    if protocol.get("governanceID"):
        scores["decentralization"] = {"score": 0, "note": "DAO governed"}
    elif protocol.get("gecko_id"):
        scores["decentralization"] = {"score": 1, "note": "Has token, governance unclear"}
    else:
        scores["decentralization"] = {"score": 2, "note": "No governance token"}
    total += scores["decentralization"]["score"]
    
    # Audit status (0-3) - separate from maturity
    if audit_count >= 2:
        scores["audit"] = {"score": 0, "note": f"{audit_count} audits"}
    elif audit_count == 1:
        scores["audit"] = {"score": 1, "note": "1 audit"}
    elif protocol.get("audit_note"):
        scores["audit"] = {"score": 2, "note": protocol.get("audit_note", "Audit issues")}
    else:
        scores["audit"] = {"score": 3, "note": "No audit"}
    total += scores["audit"]["score"]
    
    return {
        "total": min(total, 10),
        "breakdown": scores,
        "level": "low" if total <= 3 else "medium" if total <= 6 else "high"
    }


def analyze_protocol(name_or_slug: str) -> Optional[dict]:
    """
    Analyze a protocol and return detailed information.
    
    Args:
        name_or_slug: Protocol name or slug
    
    Returns:
        Protocol analysis dict
    """
    # Try as slug first
    protocol = fetch_protocol(name_or_slug)
    
    # If not found, search by name
    if not protocol:
        slug = find_protocol_slug(name_or_slug)
        if slug:
            protocol = fetch_protocol(slug)
    
    if not protocol:
        return None
    
    # Get chains - handle various formats
    chains = protocol.get("chains", [])
    if isinstance(chains, dict):
        chains = list(chains.keys())
    elif not isinstance(chains, list):
        chains = []
    
    # Get TVL by chain - handle various formats
    chain_tvl = {}
    raw_chain_tvl = protocol.get("chainTvls") or protocol.get("chainTvl") or {}
    if isinstance(raw_chain_tvl, dict):
        for chain, tvl_data in raw_chain_tvl.items():
            if isinstance(tvl_data, (int, float)):
                chain_tvl[chain] = tvl_data
            elif isinstance(tvl_data, list) and len(tvl_data) > 0:
                # Historical data - get latest
                latest = tvl_data[-1]
                if isinstance(latest, dict):
                    # Try different field names
                    val = latest.get("totalLiquidityUSD") or latest.get("tvl") or 0
                    if isinstance(val, (int, float)):
                        chain_tvl[chain] = val
            elif isinstance(tvl_data, dict):
                # Some protocols nest TVL data
                val = tvl_data.get("tvl", 0)
                if isinstance(val, (int, float)):
                    chain_tvl[chain] = val
    
    # Calculate total TVL from chain TVLs if main tvl is 0 or invalid
    raw_tvl = protocol.get("tvl", 0)
    if isinstance(raw_tvl, (int, float)):
        total_tvl = raw_tvl
    elif isinstance(raw_tvl, list) and len(raw_tvl) > 0:
        # If tvl is a list of historical data, get the latest
        latest = raw_tvl[-1]
        if isinstance(latest, dict):
            total_tvl = latest.get("totalLiquidityUSD") or latest.get("tvl", 0)
        else:
            total_tvl = 0
    elif isinstance(raw_tvl, dict):
        total_tvl = raw_tvl.get("tvl", 0)
    else:
        total_tvl = 0
    
    # Fallback: sum chain TVLs if total is 0
    if total_tvl == 0 and chain_tvl:
        total_tvl = sum(v for v in chain_tvl.values() if isinstance(v, (int, float)))
    
    # Calculate risk with total_tvl (must be after total_tvl is computed)
    risk = calculate_risk_score(protocol, total_tvl)
    def safe_change(key):
        val = protocol.get(key, 0)
        if isinstance(val, (int, float)):
            return val
        return 0
    
    # Build analysis with safe defaults
    analysis = {
        "name": protocol.get("name", name_or_slug),
        "slug": protocol.get("slug", name_or_slug.lower().replace(" ", "-")),
        "logo": protocol.get("logo", ""),
        "url": protocol.get("url", ""),
        "description": protocol.get("description", ""),
        "category": protocol.get("category", "Unknown"),
        "chains": chains,
        "tvl": {
            "total": total_tvl,
            "by_chain": chain_tvl,
            "change_24h": safe_change("change_1d"),
            "change_7d": safe_change("change_7d")
        },
        "risk": risk,
        "audits": [
            {
                "name": a.get("name", "Unknown") if isinstance(a, dict) else str(a),
                "link": a.get("link", "") if isinstance(a, dict) else "",
                "time": a.get("time", "") if isinstance(a, dict) else ""
            }
            for a in (protocol.get("audits", []) if isinstance(protocol.get("audits"), list) else [protocol.get("audits")] if protocol.get("audits") else [])
            if isinstance(a, (dict, str))
        ],
        "exploits": protocol.get("exploits", []) if isinstance(protocol.get("exploits"), list) else [],
        "governance": {
            "has_token": bool(protocol.get("gecko_id")),
            "token_name": protocol.get("token_name", ""),
            "token_symbol": protocol.get("token_symbol", "")
        },
        "social": {
            "twitter": protocol.get("twitter", ""),
            "discord": protocol.get("discord", ""),
            "telegram": protocol.get("telegram", "")
        },
        "defillama_url": f"https://defillama.com/protocol/{protocol.get('slug', name_or_slug)}"
    }
    
    return analysis


def format_report(analysis: dict, output_format: str = "markdown") -> str:
    """Format protocol analysis as report."""
    if not analysis:
        return "Protocol not found."
    
    if output_format == "json":
        return json.dumps(analysis, indent=2)
    
    # Markdown format
    lines = [
        f"# Protocol Analysis: {analysis['name']}",
        "",
        f"**Category**: {analysis['category']}",
        f"**Chains**: {', '.join(analysis['chains'])}",
        f"**Website**: {analysis['url']}",
        "",
        "---",
        "",
        "## 📊 TVL Overview",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total TVL | ${analysis['tvl']['total']:,.0f} |",
        f"| 24h Change | {analysis['tvl']['change_24h']:.2f}% |",
        f"| 7d Change | {analysis['tvl']['change_7d']:.2f}% |",
        ""
    ]
    
    if analysis['tvl']['by_chain']:
        lines.extend([
            "### TVL by Chain",
            "",
            "| Chain | TVL |",
            "|-------|-----|"
        ])
        for chain, tvl in sorted(analysis['tvl']['by_chain'].items(), 
                                   key=lambda x: x[1], reverse=True)[:5]:
            lines.append(f"| {chain} | ${tvl:,.0f} |")
        lines.append("")
    
    lines.extend([
        "---",
        "",
        "## ⚠️ Risk Assessment",
        "",
        f"| Factor | Score | Notes |",
        f"|--------|-------|-------|"
    ])
    
    for factor, data in analysis['risk']['breakdown'].items():
        lines.append(f"| {factor.title()} | {data['score']}/3 | {data['note']} |")
    
    lines.extend([
        f"| **Total** | **{analysis['risk']['total']}/10** | **{analysis['risk']['level'].upper()} RISK** |",
        ""
    ])
    
    if analysis['exploits']:
        lines.extend([
            "### 🚨 Known Exploits",
            ""
        ])
        for exploit in analysis['exploits']:
            lines.append(f"- {exploit}")
        lines.append("")
    
    lines.extend([
        "---",
        "",
        "## 🔐 Audits",
        ""
    ])
    
    if analysis['audits']:
        for audit in analysis['audits']:
            if audit['link']:
                lines.append(f"- [{audit['name']}]({audit['link']}) ({audit['time'] or 'N/A'})")
            elif audit['name'].isdigit():
                lines.append(f"- {audit['name']} audits")
            else:
                lines.append(f"- {audit['name']}")
    else:
        lines.append("No audits found.")
    
    lines.extend([
        "",
        "---",
        "",
        "## 🏛️ Governance",
        "",
        f"- **Token**: {analysis['governance']['token_symbol'] or 'No governance token'}",
        f"- **Decentralized**: {'Yes' if analysis['governance']['has_token'] else 'No'}",
        ""
    ])
    
    if analysis['social']['twitter'] or analysis['social']['discord']:
        lines.extend([
            "---",
            "",
            "## 📱 Social",
            ""
        ])
        if analysis['social']['twitter']:
            lines.append(f"- Twitter: {analysis['social']['twitter']}")
        if analysis['social']['discord']:
            lines.append(f"- Discord: {analysis['social']['discord']}")
        if analysis['social']['telegram']:
            lines.append(f"- Telegram: {analysis['social']['telegram']}")
    
    lines.extend([
        "",
        "---",
        "",
        f"📊 [View on DefiLlama]({analysis['defillama_url']})"
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze a DeFi protocol")
    parser.add_argument("--protocol", required=True, help="Protocol name or slug")
    parser.add_argument("--output", choices=["markdown", "json"], default="markdown",
                        help="Output format")
    
    args = parser.parse_args()
    
    analysis = analyze_protocol(args.protocol)
    
    if not analysis:
        print(f"Protocol '{args.protocol}' not found.", file=sys.stderr)
        sys.exit(1)
    
    print(format_report(analysis, args.output))


if __name__ == "__main__":
    main()