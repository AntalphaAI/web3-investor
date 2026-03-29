#!/usr/bin/env python3
"""
Unit tests for find_opportunities.py

Run: python -m pytest tests/test_find_opportunities.py -v
"""

import sys
import os
import pytest

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
    CHAIN_MAPPING,
    SLUG_MAPPING,
)


# ============================================================================
# Test safe_get
# ============================================================================


class TestSafeGet:
    def test_normal_dict(self):
        assert safe_get({"a": 1}, "a") == 1

    def test_missing_key(self):
        assert safe_get({"a": 1}, "b") is None

    def test_missing_key_with_default(self):
        assert safe_get({"a": 1}, "b", "default") == "default"

    def test_none_data(self):
        assert safe_get(None, "a") is None

    def test_non_dict_data(self):
        assert safe_get("string", "a") is None
        assert safe_get(123, "a") is None
        assert safe_get([1, 2], "a") is None

    def test_null_value(self):
        assert safe_get({"a": None}, "a") is None
        assert safe_get({"a": None}, "a", "default") == "default"


# ============================================================================
# Test safe_float
# ============================================================================


class TestSafeFloat:
    def test_normal_float(self):
        assert safe_float(3.14) == 3.14

    def test_int_to_float(self):
        assert safe_float(42) == 42.0

    def test_string_to_float(self):
        assert safe_float("3.14") == 3.14
        assert safe_float("100") == 100.0

    def test_none(self):
        assert safe_float(None) == 0.0

    def test_invalid_string(self):
        assert safe_float("abc") == 0.0

    def test_custom_default(self):
        assert safe_float(None, -1.0) == -1.0


# ============================================================================
# Test safe_numeric (NEW in v1.1.0)
# ============================================================================


class TestSafeNumeric:
    def test_int(self):
        assert safe_numeric(42) == 42.0

    def test_float(self):
        assert safe_numeric(3.14) == 3.14

    def test_string_number(self):
        assert safe_numeric("100") == 100.0
        assert safe_numeric("3.14") == 3.14

    def test_string_invalid(self):
        assert safe_numeric("abc") == 0.0

    def test_list_of_numbers(self):
        assert safe_numeric([1, 2, 3]) == 6.0

    def test_list_of_dicts_with_tvl(self):
        data = [{"tvlUsd": 100}, {"tvlUsd": 200}]
        assert safe_numeric(data) == 300.0

    def test_list_of_dicts_with_totalLiquidityUSD(self):
        data = [{"totalLiquidityUSD": 500}]
        assert safe_numeric(data) == 500.0

    def test_dict_with_tvl(self):
        assert safe_numeric({"tvlUsd": 1000}) == 1000.0

    def test_dict_with_totalLiquidityUSD(self):
        assert safe_numeric({"totalLiquidityUSD": 500}) == 500.0

    def test_dict_without_tvl_fields(self):
        assert safe_numeric({"other": 123}) == 0.0

    def test_none(self):
        assert safe_numeric(None) == 0.0

    def test_custom_default(self):
        assert safe_numeric(None, -1.0) == -1.0


# ============================================================================
# Test safe_list_len (NEW in v1.1.0)
# ============================================================================


class TestSafeListLen:
    def test_list(self):
        assert safe_list_len([1, 2, 3]) == 3
        assert safe_list_len([]) == 0

    def test_dict(self):
        assert safe_list_len({"a": 1, "b": 2}) == 2

    def test_string_number(self):
        assert safe_list_len("2") == 2
        assert safe_list_len("5") == 5

    def test_string_non_numeric(self):
        assert safe_list_len("abc") == 1
        assert safe_list_len("") == 0

    def test_int(self):
        assert safe_list_len(3) == 3
        assert safe_list_len(0) == 0

    def test_float(self):
        assert safe_list_len(2.5) == 2

    def test_none(self):
        assert safe_list_len(None) == 0


# ============================================================================
# Test safe_list
# ============================================================================


class TestSafeList:
    def test_list(self):
        assert safe_list([1, 2]) == [1, 2]

    def test_none(self):
        assert safe_list(None) == []

    def test_other_types(self):
        assert safe_list("abc") == []
        assert safe_list(123) == []


# ============================================================================
# Test safe_str
# ============================================================================


class TestSafeStr:
    def test_string(self):
        assert safe_str("hello") == "hello"

    def test_none(self):
        assert safe_str(None) == ""

    def test_other_types(self):
        assert safe_str(123) == "123"
        assert safe_str(3.14) == "3.14"


# ============================================================================
# Test normalize_chain
# ============================================================================


class TestNormalizeChain:
    def test_known_chains(self):
        assert normalize_chain("ethereum") == "Ethereum"
        assert normalize_chain("eth") == "Ethereum"
        assert normalize_chain("base") == "Base"
        assert normalize_chain("arbitrum") == "Arbitrum"

    def test_case_insensitive(self):
        assert normalize_chain("ETHEREUM") == "Ethereum"
        assert normalize_chain("ETH") == "Ethereum"

    def test_unknown_chain(self):
        assert normalize_chain("unknown") == "unknown"


# ============================================================================
# Test normalize_slug (NEW in v1.1.0)
# ============================================================================


class TestNormalizeSlug:
    def test_known_slugs(self):
        assert normalize_slug("aave") == "aave-v3"
        assert normalize_slug("compound") == "compound-v3"
        assert normalize_slug("uniswap") == "uniswap-v3"

    def test_case_sensitive(self):
        # SLUG_MAPPING keys are lowercase
        assert normalize_slug("Aave") == "Aave"  # Not mapped (case sensitive)

    def test_unknown_slug(self):
        assert normalize_slug("unknown-protocol") == "unknown-protocol"

    def test_empty_slug(self):
        assert normalize_slug("") == ""
        assert normalize_slug(None) == None


# ============================================================================
# Test detect_reward_type
# ============================================================================


class TestDetectRewardType:
    def test_no_rewards(self):
        pool = {"rewardTokens": []}
        assert detect_reward_type(pool) == "none"

    def test_single_reward(self):
        pool = {"rewardTokens": ["0x123"]}
        assert detect_reward_type(pool) == "single"

    def test_multi_rewards(self):
        pool = {"rewardTokens": ["0x123", "0x456"]}
        assert detect_reward_type(pool) == "multi"

    def test_none_rewards(self):
        pool = {}
        assert detect_reward_type(pool) == "none"


# ============================================================================
# Test detect_il_risk
# ============================================================================


class TestDetectIlRisk:
    def test_dex_category(self):
        pool = {"underlyingTokens": ["0x123"]}
        assert detect_il_risk(pool, "DEX") == True
        assert detect_il_risk(pool, "AMM") == True

    def test_multi_asset_non_stable(self):
        pool = {"underlyingTokens": ["0x123", "0x456"], "stablecoin": False}
        assert detect_il_risk(pool, "lending") == True

    def test_multi_asset_stable(self):
        pool = {"underlyingTokens": ["0x123", "0x456"], "stablecoin": True}
        assert detect_il_risk(pool, "lending") == False

    def test_single_asset(self):
        pool = {"underlyingTokens": ["0x123"]}
        assert detect_il_risk(pool, "lending") == False


# ============================================================================
# Test detect_underlying_type
# ============================================================================


class TestDetectUnderlyingType:
    def test_rwa_keywords(self):
        pool = {}
        assert detect_underlying_type(pool, "", "TBILL") == "rwa"
        assert detect_underlying_type(pool, "", "USDBC") == "rwa"
        assert detect_underlying_type(pool, "RWA Pool", "") == "rwa"

    def test_onchain_categories(self):
        pool = {}
        assert detect_underlying_type(pool, "Lending", "USDC") == "onchain"
        assert detect_underlying_type(pool, "Yield", "ETH") == "onchain"

    def test_mixed(self):
        pool = {"underlyingTokens": ["0x123", "0x456"]}
        assert detect_underlying_type(pool, "other", "LP") == "mixed"

    def test_unknown(self):
        pool = {"underlyingTokens": ["0x123"]}
        assert detect_underlying_type(pool, "other", "TOKEN") == "unknown"


# ============================================================================
# Test extract_actionable_addresses
# ============================================================================


class TestExtractActionableAddresses:
    def test_pool_address(self):
        pool = {"pool": "0x1234567890123456789012345678901234567890"}
        protocol = {}
        registry = {}

        result = extract_actionable_addresses(pool, protocol, registry)
        assert result["has_actionable_address"] == True
        assert (
            "0x1234567890123456789012345678901234567890"
            in result["deposit_contract_candidates"]
        )

    def test_underlying_tokens(self):
        pool = {
            "pool": "not-an-address",
            "underlyingTokens": ["0x1111111111111111111111111111111111111111"],
        }
        protocol = {}
        registry = {}

        result = extract_actionable_addresses(pool, protocol, registry)
        assert result["has_actionable_address"] == True
        assert len(result["underlying_token_addresses"]) == 1

    def test_registry_match(self):
        pool = {"project": "aave-v3"}
        protocol = {}
        registry = {
            "aave-v3": {
                "primary_contract": "0x2222222222222222222222222222222222222222",
                "docs_url": "https://docs.aave.com",
            }
        }

        result = extract_actionable_addresses(pool, protocol, registry)
        assert result["protocol_registry_match"] == True
        assert (
            result["primary_contract"] == "0x2222222222222222222222222222222222222222"
        )
        assert result["docs_url"] == "https://docs.aave.com"

    def test_no_addresses(self):
        pool = {"pool": "not-an-address", "underlyingTokens": []}
        protocol = {}
        registry = {}

        result = extract_actionable_addresses(pool, protocol, registry)
        assert result["has_actionable_address"] == False


# ============================================================================
# Test collect_risk_signals (with total_tvl parameter)
# ============================================================================


class TestCollectRiskSignals:
    def test_basic_signals(self):
        pool = {
            "project": "test-protocol",
            "symbol": "USDC",
            "chain": "Ethereum",
            "apy": 5.0,
            "tvlUsd": 1000000,
            "stablecoin": True,
        }
        protocol = {"audits": ["audit1.pdf", "audit2.pdf"]}
        registry = {}

        result = collect_risk_signals(pool, protocol, registry)
        assert result["symbol"] == "USDC"
        assert result["chain"] == "Ethereum"
        assert result["apy"] == 5.0
        assert result["has_audit"] == True
        assert result["audit_count"] == 2
        assert result["audit_display"] == "2 audits"

    def test_audit_string_number(self):
        """Test handling of audits as string number like '2'"""
        pool = {"project": "test", "symbol": "TEST"}
        protocol = {"audits": "2"}
        registry = {}

        result = collect_risk_signals(pool, protocol, registry)
        assert result["audit_count"] == 2
        assert result["has_audit"] == True
        assert result["audit_display"] == "2 audits"

    def test_audit_int(self):
        """Test handling of audits as integer"""
        pool = {"project": "test", "symbol": "TEST"}
        protocol = {"audits": 3}
        registry = {}

        result = collect_risk_signals(pool, protocol, registry)
        assert result["audit_count"] == 3
        assert result["has_audit"] == True
        assert result["audit_display"] == "3 audits"

    def test_no_audits(self):
        pool = {"project": "test", "symbol": "TEST"}
        protocol = {}
        registry = {}

        result = collect_risk_signals(pool, protocol, registry)
        assert result["audit_count"] == 0
        assert result["has_audit"] == False
        assert result["audit_display"] == "No audits"

    def test_total_tvl_parameter(self):
        """Test that total_tvl parameter is used correctly"""
        pool = {"project": "test", "symbol": "TEST", "tvlUsd": 100}
        protocol = {}
        registry = {}

        # Without total_tvl
        result1 = collect_risk_signals(pool, protocol, registry)
        assert result1["tvl_usd"] == 100.0

        # With total_tvl
        result2 = collect_risk_signals(pool, protocol, registry, total_tvl=5000)
        assert result2["tvl_usd"] == 5000.0


# ============================================================================
# Integration test (if network available)
# ============================================================================


class TestIntegration:
    @pytest.mark.slow
    def test_fetch_yields(self):
        """Test actual API call (marked as slow)"""
        from find_opportunities import fetch_yields

        result = fetch_yields()
        assert "data" in result
        assert isinstance(result["data"], list)

    @pytest.mark.slow
    def test_find_opportunities(self):
        """Test full flow (marked as slow)"""
        from find_opportunities import find_opportunities

        opps = find_opportunities(
            min_apy=5,
            chain="Ethereum",
            min_tvl=10000000,
            limit=3,
            include_execution_readiness=False,
        )

        assert len(opps) <= 3
        if opps:
            assert "pool" in opps[0]
            assert "apy" in opps[0]
            assert "tvl_usd" in opps[0]
            assert "risk_signals" in opps[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
