---
name: web3-investor
version: 2.0.3
description: AI-friendly Web3 investment infrastructure for discovering and analyzing DeFi yield opportunities via MCP. Use when users want to (1) find DeFi investment opportunities on ethereum/base/arbitrum/optimism, (2) analyze specific yield products in detail, (3) compare multiple investment options, (4) get personalized recommendations based on risk tolerance. All data fetched from remote MCP server - no local API keys needed.
author: Antalpha AI Team
homepage: https://www.antalpha.com/
metadata:
  openclaw:
    requires:
      env: []
notes:
  This skill is a thin wrapper around the MCP server at https://mcp-skills.ai.antalpha.com/mcp
  No local API keys required - all requests handled by the server.
---

# Web3 Investor Skill

> **Purpose**: Enable AI agents to discover and analyze DeFi investment opportunities.
> **Architecture**: Thin MCP client wrapper - all logic runs on remote server.

---

## ⚠️ Critical Rules

### Rule 1: Discovery First
When user asks for investment advice:
```
❌ WRONG: Give generic advice immediately
✅ CORRECT:
   1. Collect preferences (chain, risk tolerance)
   2. Run discovery via MCP
   3. Analyze data
   4. Provide data-backed recommendations
```

### Rule 2: Server Handles All Logic
- This skill is a **thin wrapper** - it only forwards requests
- All data fetching, analysis, and API key management happens on the server
- No local environment variables or API keys needed

---

## 🎯 Quick Start

### Step 1: Collect Preferences

| Preference | Options | Why It Matters |
|------------|---------|----------------|
| **Chain** | ethereum, base, arbitrum, optimism | Determines blockchain to search |
| **Min APY** | Any number (%) | Filter by yield |
| **Risk** | conservative, moderate, aggressive | Risk tolerance |

### Step 2: Run Discovery

```bash
python3 scripts/mcp_client.py discover \
  --chain ethereum \
  --min-apy 5 \
  --limit 5
```

### Step 3: Analyze

```bash
python3 scripts/mcp_client.py analyze \
  --product-id aave-usdc-base \
  --depth detailed
```

---

## 📁 Project Structure

```
web3-investor/
├── scripts/
│   └── mcp_client.py          # MCP client wrapper
├── config/
│   └── config.json            # Legacy config (unused)
└── SKILL.md
```

---

## 🔧 Available Commands

| Command | MCP Tool | Description |
|---------|----------|-------------|
| `discover` | `investor_discover` | Find DeFi yield opportunities |
| `analyze` | `investor_analyze` | Deep analysis of single opportunity |
| `compare` | `investor_compare` | Compare multiple opportunities |
| `feedback` | `investor_feedback` | Submit feedback on recommendations |
| `confirm-intent` | `investor_confirm_intent` | Confirm user intent after clarification |
| `get-intent` | `investor_get_stored_intent` | Get stored intent for session |

### discover
```bash
python3 scripts/mcp_client.py discover \
  --chain <ethereum|base|arbitrum|optimism> \
  --min-apy <number> \
  [--max-apy <number>] \
  [--stablecoin-only] \
  [--limit <1-10>] \
  [--session-id <id>] \
  [--natural-language <query>]
```

### analyze
```bash
python3 scripts/mcp_client.py analyze \
  --product-id <id> \
  [--depth basic|detailed|full] \
  [--no-history]
```

### compare
```bash
python3 scripts/mcp_client.py compare \
  --ids <id1> <id2> [<id3>...]
```

### feedback
```bash
python3 scripts/mcp_client.py feedback \
  --product-id <id> \
  --feedback <helpful|not_helpful|invested|dismissed> \
  [--reason <text>]
```

### confirm-intent
```bash
python3 scripts/mcp_client.py confirm-intent \
  --session-id <id> \
  --type <intent_type> \
  --risk <risk_profile> \
  [--capital-nature <nature>] \
  [--liquidity-need <need>]
```

### get-intent
```bash
python3 scripts/mcp_client.py get-intent \
  --session-id <id>
```

---

## 📊 MCP Tools Reference

| Tool | Purpose | Key Response Fields |
|------|---------|--------------------|
| `investor_discover` | Find yield opportunities | recommendations[], intent{}, search_stats |
| `investor_analyze` | Deep analysis | product{}, historical_data, llm_insights |
| `investor_compare` | Multi-opportunity comparison | products[], comparisons[], recommendation |
| `investor_feedback` | Feedback submission | acknowledged |
| `investor_confirm_intent` | Intent confirmation | acknowledged, session_id |
| `investor_get_stored_intent` | Retrieve stored intent | found, intent{} |

---

## 🧪 Example Sessions

### Session 1: Find and Analyze
```
User: Find me ETH lending on Base with >5% APY
Agent:
  python3 scripts/mcp_client.py discover --chain base --min-apy 5

User: Analyze the best one
Agent:
  python3 scripts/mcp_client.py analyze --product-id aave-eth-base --depth detailed
```

### Session 2: Compare Opportunities
```
User: Compare aave-usdc-base vs compound-usdc-ethereum
Agent:
  python3 scripts/mcp_client.py compare --ids aave-usdc-base compound-usdc-ethereum
```

### Session 3: Intent Clarification Flow
```
User: I want to invest in DeFi
Agent:
  # Server returns NEEDS_CLARIFICATION
  python3 scripts/mcp_client.py discover --natural-language "I want to invest in DeFi"
  # Returns clarification question

User: [Selects: stablecoin, moderate risk, 1 month horizon]
Agent:
  python3 scripts/mcp_client.py confirm-intent \
    --session-id <id> \
    --type stablecoin \
    --risk moderate

User: Now find opportunities
Agent:
  python3 scripts/mcp_client.py discover --session-id <id>
```

### Session 4: Provide Feedback
```
User: The aave recommendation was helpful
Agent:
  python3 scripts/mcp_client.py feedback \
    --product-id aave-usdc-base \
    --feedback helpful
```

---

## 🔒 Security Notes

- All API keys managed server-side
- No sensitive data stored locally
- Requests go directly to MCP server: `https://mcp-skills.ai.antalpha.com/mcp`

---

**Maintainer**: Web3 Investor Skill Team
**Registry**: https://clawhub.com/skills/web3-investor
**License**: MIT
