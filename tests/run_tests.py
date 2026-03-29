#!/usr/bin/env python3
"""
Simple test runner for find_opportunities.py (no pytest required)

Run: python3 tests/run_tests.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "scripts", "discovery")
)

from find_opportunities import (
    safe_get,
    safe_float,
    safe_numeric,
    safe_list,
    safe_list_len,
    safe_str,
    normalize_chain,
    normalize_slug,
    detect_reward_type,
    detect_il_risk,
    detect_underlying_type,
    extract_actionable_addresses,
    collect_risk_signals,
)

# Test results
passed = 0
failed = 0
errors = []


def assert_eq(actual, expected, test_name):
    global passed, failed
    if actual == expected:
        passed += 1
        print(f"  ✅ {test_name}")
    else:
        failed += 1
        errors.append(f"{test_name}: expected {expected}, got {actual}")
        print(f"  ❌ {test_name}: expected {expected}, got {actual}")


def assert_true(condition, test_name):
    assert_eq(condition, True, test_name)


def assert_false(condition, test_name):
    assert_eq(condition, False, test_name)


# ============================================================================
# Test safe_get
# ============================================================================

print("\n📦 Testing safe_get...")
assert_eq(safe_get({"a": 1}, "a"), 1, "normal_dict")
assert_eq(safe_get({"a": 1}, "b"), None, "missing_key")
assert_eq(safe_get({"a": 1}, "b", "default"), "default", "missing_key_with_default")
assert_eq(safe_get(None, "a"), None, "none_data")
assert_eq(safe_get("string", "a"), None, "non_dict_data")
assert_eq(safe_get({"a": None}, "a"), None, "null_value")


# ============================================================================
# Test safe_float
# ============================================================================

print("\n📦 Testing safe_float...")
assert_eq(safe_float(3.14), 3.14, "normal_float")
assert_eq(safe_float(42), 42.0, "int_to_float")
assert_eq(safe_float("3.14"), 3.14, "string_to_float")
assert_eq(safe_float(None), 0.0, "none")
assert_eq(safe_float("abc"), 0.0, "invalid_string")
assert_eq(safe_float(None, -1.0), -1.0, "custom_default")


# ============================================================================
# Test safe_numeric (NEW in v1.1.0)
# ============================================================================

print("\n📦 Testing safe_numeric (v1.1.0)...")
assert_eq(safe_numeric(42), 42.0, "int")
assert_eq(safe_numeric(3.14), 3.14, "float")
assert_eq(safe_numeric("100"), 100.0, "string_number")
assert_eq(safe_numeric("abc"), 0.0, "string_invalid")
assert_eq(safe_numeric([1, 2, 3]), 6.0, "list_of_numbers")
assert_eq(safe_numeric([{"tvlUsd": 100}, {"tvlUsd": 200}]), 300.0, "list_of_dicts_tvl")
assert_eq(
    safe_numeric([{"totalLiquidityUSD": 500}]), 500.0, "list_of_dicts_totalLiquidity"
)
assert_eq(safe_numeric({"tvlUsd": 1000}), 1000.0, "dict_with_tvl")
assert_eq(safe_numeric({"totalLiquidityUSD": 500}), 500.0, "dict_with_totalLiquidity")
assert_eq(safe_numeric(None), 0.0, "none")


# ============================================================================
# Test safe_list_len (NEW in v1.1.0)
# ============================================================================

print("\n📦 Testing safe_list_len (v1.1.0)...")
assert_eq(safe_list_len([1, 2, 3]), 3, "list")
assert_eq(safe_list_len([]), 0, "empty_list")
assert_eq(safe_list_len({"a": 1, "b": 2}), 2, "dict")
assert_eq(safe_list_len("2"), 2, "string_number")
assert_eq(safe_list_len("abc"), 1, "string_non_numeric")
assert_eq(safe_list_len(""), 0, "empty_string")
assert_eq(safe_list_len(3), 3, "int")
assert_eq(safe_list_len(0), 0, "zero")
assert_eq(safe_list_len(None), 0, "none")


# ============================================================================
# Test safe_list
# ============================================================================

print("\n📦 Testing safe_list...")
assert_eq(safe_list([1, 2]), [1, 2], "list")
assert_eq(safe_list(None), [], "none")
assert_eq(safe_list("abc"), [], "string")


# ============================================================================
# Test safe_str
# ============================================================================

print("\n📦 Testing safe_str...")
assert_eq(safe_str("hello"), "hello", "string")
assert_eq(safe_str(None), "", "none")
assert_eq(safe_str(123), "123", "int")


# ============================================================================
# Test normalize_chain
# ============================================================================

print("\n📦 Testing normalize_chain...")
assert_eq(normalize_chain("ethereum"), "Ethereum", "ethereum")
assert_eq(normalize_chain("eth"), "Ethereum", "eth")
assert_eq(normalize_chain("base"), "Base", "base")
assert_eq(normalize_chain("ETHEREUM"), "Ethereum", "case_insensitive")
assert_eq(normalize_chain("unknown"), "unknown", "unknown")


# ============================================================================
# Test normalize_slug (NEW in v1.1.0)
# ============================================================================

print("\n📦 Testing normalize_slug (v1.1.0)...")
assert_eq(normalize_slug("aave"), "aave-v3", "aave")
assert_eq(normalize_slug("compound"), "compound-v3", "compound")
assert_eq(normalize_slug("uniswap"), "uniswap-v3", "uniswap")
assert_eq(normalize_slug("unknown"), "unknown", "unknown")
assert_eq(normalize_slug(""), "", "empty")


# ============================================================================
# Test detect_reward_type
# ============================================================================

print("\n📦 Testing detect_reward_type...")
assert_eq(detect_reward_type({"rewardTokens": []}), "none", "no_rewards")
assert_eq(detect_reward_type({"rewardTokens": ["0x123"]}), "single", "single")
assert_eq(detect_reward_type({"rewardTokens": ["0x123", "0x456"]}), "multi", "multi")
assert_eq(detect_reward_type({}), "none", "missing")


# ============================================================================
# Test detect_il_risk
# ============================================================================

print("\n📦 Testing detect_il_risk...")
assert_true(detect_il_risk({"underlyingTokens": ["0x123"]}, "DEX"), "dex_category")
assert_true(
    detect_il_risk(
        {"underlyingTokens": ["0x123", "0x456"], "stablecoin": False}, "lending"
    ),
    "multi_asset_non_stable",
)
assert_false(
    detect_il_risk(
        {"underlyingTokens": ["0x123", "0x456"], "stablecoin": True}, "lending"
    ),
    "multi_asset_stable",
)
assert_false(detect_il_risk({"underlyingTokens": ["0x123"]}, "lending"), "single_asset")


# ============================================================================
# Test detect_underlying_type
# ============================================================================

print("\n📦 Testing detect_underlying_type...")
assert_eq(detect_underlying_type({}, "", "TBILL"), "rwa", "rwa_keyword")
assert_eq(detect_underlying_type({}, "Lending", "USDC"), "onchain", "onchain_category")
assert_eq(
    detect_underlying_type({"underlyingTokens": ["0x123", "0x456"]}, "other", "LP"),
    "mixed",
    "mixed",
)
assert_eq(
    detect_underlying_type({"underlyingTokens": ["0x123"]}, "other", "TOKEN"),
    "unknown",
    "unknown",
)


# ============================================================================
# Test extract_actionable_addresses
# ============================================================================

print("\n📦 Testing extract_actionable_addresses...")

# Pool address
pool = {"pool": "0x1234567890123456789012345678901234567890"}
result = extract_actionable_addresses(pool, {}, {})
assert_true(result["has_actionable_address"], "pool_address")

# Underlying tokens
pool = {
    "pool": "not-an-address",
    "underlyingTokens": ["0x1111111111111111111111111111111111111111"],
}
result = extract_actionable_addresses(pool, {}, {})
assert_true(result["has_actionable_address"], "underlying_tokens")

# Registry match
pool = {"project": "aave-v3"}
registry = {
    "aave-v3": {
        "primary_contract": "0x2222222222222222222222222222222222222222",
        "docs_url": "https://docs.aave.com",
    }
}
result = extract_actionable_addresses(pool, {}, registry)
assert_true(result["protocol_registry_match"], "registry_match")
assert_eq(
    result["primary_contract"],
    "0x2222222222222222222222222222222222222222",
    "primary_contract",
)

# No addresses
pool = {"pool": "not-an-address", "underlyingTokens": []}
result = extract_actionable_addresses(pool, {}, {})
assert_false(result["has_actionable_address"], "no_addresses")


# ============================================================================
# Test collect_risk_signals (NEW total_tvl parameter)
# ============================================================================

print("\n📦 Testing collect_risk_signals (v1.1.0)...")

# Basic signals
pool = {
    "project": "test",
    "symbol": "USDC",
    "chain": "Ethereum",
    "apy": 5.0,
    "tvlUsd": 1000000,
}
protocol = {"audits": ["audit1.pdf", "audit2.pdf"]}
result = collect_risk_signals(pool, protocol, {})
assert_eq(result["symbol"], "USDC", "symbol")
assert_eq(result["chain"], "Ethereum", "chain")
assert_eq(result["apy"], 5.0, "apy")
assert_true(result["has_audit"], "has_audit")
assert_eq(result["audit_count"], 2, "audit_count")
assert_eq(result["audit_display"], "2 audits", "audit_display")

# Audit string number
pool = {"project": "test", "symbol": "TEST"}
protocol = {"audits": "2"}
result = collect_risk_signals(pool, protocol, {})
assert_eq(result["audit_count"], 2, "audit_string_count")
assert_eq(result["audit_display"], "2 audits", "audit_string_display")

# Audit int
protocol = {"audits": 3}
result = collect_risk_signals(pool, protocol, {})
assert_eq(result["audit_count"], 3, "audit_int_count")

# No audits
protocol = {}
result = collect_risk_signals(pool, protocol, {})
assert_eq(result["audit_display"], "No audits", "no_audits_display")

# total_tvl parameter
pool = {"project": "test", "symbol": "TEST", "tvlUsd": 100}
result1 = collect_risk_signals(pool, {}, {})
assert_eq(result1["tvl_usd"], 100.0, "tvl_without_param")

result2 = collect_risk_signals(pool, {}, {}, total_tvl=5000)
assert_eq(result2["tvl_usd"], 5000.0, "tvl_with_param")


# ============================================================================
# Summary
# ============================================================================

print("\n" + "=" * 60)
print(f"📊 Test Results: {passed} passed, {failed} failed")
print("=" * 60)

if errors:
    print("\n❌ Failed tests:")
    for err in errors:
        print(f"  - {err}")
    sys.exit(1)
else:
    print("\n✅ All tests passed!")
    sys.exit(0)
