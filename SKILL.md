---
name: web3-investor
version: 3.7.2
description: AI-friendly Web3 investment infrastructure for discovering and analyzing DeFi yield opportunities via MCP. Use when users want to discover investment opportunities, analyze products, compare options, or get personalized recommendations. All logic runs on remote MCP server - no local API keys needed.
author: Antalpha AI Team
homepage: https://www.antalpha.com/
---

# Web3-Investor

> DeFi investment intelligence — discover, analyze, compare, and recommend yield opportunities.
> **Version**: 3.7.2 — 客户端清理：移除已下线工具（feedback/confirm-intent/get-intent）

---

## 🛠 Tools (3)

| Tool | Responsibility |
|------|---------------|
| `investor_discover` | Sole entry: discovery + intent recognition + multi-round accumulation |
| `investor_analyze` | Deep analysis: LLM 5-step reasoning |
| `investor_compare` | Comparative analysis: horizontal comparison + risk-based recommendation |

---

## ⚡ 30秒快速开始

```bash
cd /path/to/skills/web3-investor

# 1. Discover opportunities
./scripts/run.sh discover --chain ethereum --min-apy 5 --limit 5

# 2. Deep analysis
./scripts/run.sh analyze --product-id <id> --depth detailed

# 3. Compare products
./scripts/run.sh compare --ids <id1> <id2>
```

---

## 🎯 Scenario → Command Decision Tree

```
What does the user want?
│
├─ "Find investment opportunities" ──→ ./scripts/run.sh discover
│   ├─ Stablecoin preference → discover --chain ethereum --stablecoin-only
│   ├─ Minimum yield → discover --min-apy 5
│   └─ NEEDS_CLARIFICATION → show options to user, re-discover with refined intent + session-id
│
├─ "Deep dive into product X" ──→ ./scripts/run.sh analyze --product-id <id>
│   └─ More comprehensive → analyze --depth full
│
└─ "Compare A vs B" ──→ ./scripts/run.sh compare --ids <id1> <id2> [<id3> <id4>]
```

---

## 🔧 Command Reference

### discover — Discover Investment Opportunities

Find on-chain yield opportunities. Supports natural language intent recognition with automatic risk preference matching. Multi-round session auto-accumulates intent.

**Input**:
```bash
./scripts/run.sh discover \
  --chain <ethereum|base|arbitrum|optimism> \
  [--min-apy 5] [--max-apy 50] \
  [--stablecoin-only] \
  [--limit 5] \
  [--natural-language "stablecoin yield, conservative"] \
  [--session-id <id>]
```

**Typical Response** (PASS):
```json
{
  "gate_status": "PASS",
  "recommendations": [
    { "id": "...", "name": "Aave V3 USDC", "apy": 5.2, "tvl_usd": 1500000000, "risk_score": 25 }
  ],
  "suggested_next_actions": [
    { "action": "ask_user_to_select_product", "priority": 1 },
    { "action": "call_investor_analyze_for_details", "priority": 2 }
  ]
}
```

**Needs Clarification** (NEEDS_CLARIFICATION):
- Show `clarification.question` to user
- Show `clarification.structured_options[]` for selection
- After user selects, re-call `discover` with refined intent + same `--session-id`
- The session automatically accumulates intent across rounds — no separate confirm step needed

### analyze — Deep Analysis

LLM-powered deep analysis of a single product (5-step reasoning chain).

**Input**:
```bash
./scripts/run.sh analyze --product-id <id> [--depth basic|detailed|full]
```

**Typical Response**:
```json
{
  "product": { "name": "Aave V3 USDC", "yield": { "apy": 5.2 } },
  "llm_insights": { "yield_source": "lending_spread", "sustainability": "sustainable" },
  "analysis_meta": {
    "llm_used": true,
    "fallback_applied": false,
    "confidence_note": "Deep analysis by LLM. Insights are based on protocol data and AI reasoning."
  }
}
```

### compare — Compare Products

Side-by-side comparison with LLM-powered interpretation and risk-based recommendations.

**Input**:
```bash
./scripts/run.sh compare --ids <id1> <id2> [<id3> <id4>]
```

**Typical Response**:
```json
{
  "products": [...],
  "comparisons": [
    { "dimension": "apy", "values": {...}, "best_performer": "..." }
  ],
  "llm_comparison": {
    "narrative": "A offers higher security, while B provides better yield...",
    "risk_comparison": "...",
    "recommendation_with_reasoning": {
      "for_conservative": "Choose A because...",
      "for_aggressive": "Choose B because...",
      "key_tradeoff": "Security vs yield"
    }
  }
}
```

---

## ⚠️ FAQ

| Issue | Cause | Solution |
|-------|-------|----------|
| NEEDS_CLARIFICATION | Intent unclear | Show options to user, re-discover with refined input + session-id |
| "Product not found" | Invalid product_id | Use real id from discover results |
| analysis_meta.fallback_applied=true | LLM timeout/unavailable | Result is rule-based only, for reference |
| Network timeout | External service slow | Retry — all APIs have auto-retry with exponential backoff |
