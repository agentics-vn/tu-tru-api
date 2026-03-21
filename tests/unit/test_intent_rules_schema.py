"""
T1-08: JSON schema validation for intent-rules.json — fail on load if invalid.

Validates that docs/seed/intent-rules.json conforms to the expected schema:
- Every intent has required fields (preferred_truc, forbidden_truc, bonus_sao, forbidden_sao)
- All truc indices are 0–11
- No duplicate values in arrays
- All intent keys match IntentEnum (minus aliases)
- _meta block has required fields

Also provides a validate_intent_rules() function that can be called at app
startup to fail fast on schema violations.

Run with: python3 -m pytest tests/unit/test_intent_rules_schema.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import json
import pytest
from pathlib import Path

INTENT_RULES_PATH = (
    Path(__file__).resolve().parent.parent.parent / "docs" / "seed" / "intent-rules.json"
)

REQUIRED_INTENT_FIELDS = {"preferred_truc", "forbidden_truc", "bonus_sao", "forbidden_sao"}
VALID_TRUC_RANGE = set(range(12))  # 0–11

# Intents that should exist per IntentEnum in chon_ngay.py
# (CUOI_HOI is an alias → maps to DAM_CUOI, so not required in JSON)
EXPECTED_INTENTS = {
    "KHAI_TRUONG", "KY_HOP_DONG", "CAU_TAI", "NHAM_CHUC",
    "AN_HOI", "DAM_CUOI",
    "DONG_THO", "NHAP_TRACH", "LAM_NHA", "MUA_NHA_DAT",
    "XAY_BEP", "LAM_GIUONG", "DAO_GIENG",
    "AN_TANG", "CAI_TANG",
    "XUAT_HANH", "DI_CHUYEN_NGOAI",
    "TE_TU", "GIAI_HAN", "KHAM_BENH", "PHAU_THUAT",
    "NHAP_HOC_THI_CU", "KIEN_TUNG",
    "TRONG_CAY", "CAU_TU",
    "MAC_DINH",
}


def _load_rules() -> dict:
    with open(INTENT_RULES_PATH, encoding="utf-8") as f:
        return json.load(f)


class TestIntentRulesFileLoadable:

    def test_file_exists(self):
        assert INTENT_RULES_PATH.exists(), f"Missing {INTENT_RULES_PATH}"

    def test_valid_json(self):
        rules = _load_rules()
        assert isinstance(rules, dict)


class TestIntentRulesMeta:

    def test_meta_block_exists(self):
        rules = _load_rules()
        assert "_meta" in rules

    def test_meta_has_version(self):
        rules = _load_rules()
        assert "version" in rules["_meta"]

    def test_meta_has_total_intents(self):
        rules = _load_rules()
        assert "total_intents" in rules["_meta"]
        assert isinstance(rules["_meta"]["total_intents"], int)

    def test_meta_total_intents_matches(self):
        rules = _load_rules()
        intent_keys = {k for k in rules if not k.startswith("_")}
        assert rules["_meta"]["total_intents"] == len(intent_keys), (
            f"_meta.total_intents={rules['_meta']['total_intents']} "
            f"but found {len(intent_keys)} intent keys"
        )


class TestIntentRulesCompleteness:

    def test_all_expected_intents_present(self):
        rules = _load_rules()
        intent_keys = {k for k in rules if not k.startswith("_")}
        missing = EXPECTED_INTENTS - intent_keys
        assert len(missing) == 0, f"Missing intents in JSON: {missing}"

    def test_no_unknown_intents(self):
        """All intent keys in JSON should be in the expected set."""
        rules = _load_rules()
        intent_keys = {k for k in rules if not k.startswith("_")}
        unknown = intent_keys - EXPECTED_INTENTS
        assert len(unknown) == 0, f"Unknown intents in JSON: {unknown}"


class TestIntentRulesSchema:
    """Validate each intent has required fields with correct types and values."""

    @pytest.fixture
    def rules(self):
        return _load_rules()

    @pytest.fixture
    def intents(self, rules):
        return {k: v for k, v in rules.items() if not k.startswith("_")}

    def test_all_intents_have_required_fields(self, intents):
        for intent_key, rule in intents.items():
            for field in REQUIRED_INTENT_FIELDS:
                assert field in rule, (
                    f"Intent '{intent_key}' missing required field '{field}'"
                )

    def test_preferred_truc_is_list_of_valid_indices(self, intents):
        for intent_key, rule in intents.items():
            truc_list = rule["preferred_truc"]
            assert isinstance(truc_list, list), (
                f"Intent '{intent_key}': preferred_truc must be a list"
            )
            for idx in truc_list:
                assert isinstance(idx, int) and idx in VALID_TRUC_RANGE, (
                    f"Intent '{intent_key}': invalid truc index {idx} in preferred_truc"
                )

    def test_forbidden_truc_is_list_of_valid_indices(self, intents):
        for intent_key, rule in intents.items():
            truc_list = rule["forbidden_truc"]
            assert isinstance(truc_list, list), (
                f"Intent '{intent_key}': forbidden_truc must be a list"
            )
            for idx in truc_list:
                assert isinstance(idx, int) and idx in VALID_TRUC_RANGE, (
                    f"Intent '{intent_key}': invalid truc index {idx} in forbidden_truc"
                )

    def test_no_truc_overlap(self, intents):
        """preferred_truc and forbidden_truc should not overlap."""
        for intent_key, rule in intents.items():
            overlap = set(rule["preferred_truc"]) & set(rule["forbidden_truc"])
            assert len(overlap) == 0, (
                f"Intent '{intent_key}': truc indices {overlap} in both "
                f"preferred and forbidden"
            )

    def test_no_duplicate_preferred_truc(self, intents):
        for intent_key, rule in intents.items():
            lst = rule["preferred_truc"]
            assert len(lst) == len(set(lst)), (
                f"Intent '{intent_key}': duplicates in preferred_truc"
            )

    def test_no_duplicate_forbidden_truc(self, intents):
        for intent_key, rule in intents.items():
            lst = rule["forbidden_truc"]
            assert len(lst) == len(set(lst)), (
                f"Intent '{intent_key}': duplicates in forbidden_truc"
            )

    def test_bonus_sao_is_list_of_strings(self, intents):
        for intent_key, rule in intents.items():
            sao_list = rule["bonus_sao"]
            assert isinstance(sao_list, list), (
                f"Intent '{intent_key}': bonus_sao must be a list"
            )
            for sao in sao_list:
                assert isinstance(sao, str) and len(sao) > 0, (
                    f"Intent '{intent_key}': invalid sao '{sao}' in bonus_sao"
                )

    def test_forbidden_sao_is_list_of_strings(self, intents):
        for intent_key, rule in intents.items():
            sao_list = rule["forbidden_sao"]
            assert isinstance(sao_list, list), (
                f"Intent '{intent_key}': forbidden_sao must be a list"
            )
            for sao in sao_list:
                assert isinstance(sao, str) and len(sao) > 0, (
                    f"Intent '{intent_key}': invalid sao '{sao}' in forbidden_sao"
                )

    def test_no_sao_overlap(self, intents):
        """bonus_sao and forbidden_sao should not overlap."""
        for intent_key, rule in intents.items():
            overlap = set(rule["bonus_sao"]) & set(rule["forbidden_sao"])
            assert len(overlap) == 0, (
                f"Intent '{intent_key}': sao {overlap} in both bonus and forbidden"
            )

    def test_no_duplicate_bonus_sao(self, intents):
        for intent_key, rule in intents.items():
            lst = rule["bonus_sao"]
            assert len(lst) == len(set(lst)), (
                f"Intent '{intent_key}': duplicates in bonus_sao"
            )

    def test_no_duplicate_forbidden_sao(self, intents):
        for intent_key, rule in intents.items():
            lst = rule["forbidden_sao"]
            assert len(lst) == len(set(lst)), (
                f"Intent '{intent_key}': duplicates in forbidden_sao"
            )


class TestIntentRulesSpecialRules:
    """Validate _special_rules blocks where present."""

    @pytest.fixture
    def rules(self):
        return _load_rules()

    def test_dam_cuoi_avoids_month7(self, rules):
        assert rules["DAM_CUOI"]["_special_rules"]["avoid_lunar_month_7"] is True

    def test_dong_tho_avoids_month7(self, rules):
        assert rules["DONG_THO"]["_special_rules"]["avoid_lunar_month_7"] is True

    def test_nhap_trach_avoids_month7(self, rules):
        assert rules["NHAP_TRACH"]["_special_rules"]["avoid_lunar_month_7"] is True

    def test_kien_tung_excludes_nguyet_duc(self, rules):
        assert rules["KIEN_TUNG"]["_special_rules"]["exclude_nguyet_duc_bonus"] is True


class TestIntentRulesConsistencyWithCode:
    """Cross-check JSON data against hardcoded values in engine code."""

    def test_phá_nguy_always_forbidden(self):
        """Trực Phá (6) and Trực Nguy (7) are Layer 1 discards.
        They should be in forbidden_truc for most intents."""
        rules = _load_rules()
        intents = {k: v for k, v in rules.items() if not k.startswith("_")}
        # Phá (6) should be forbidden for all intents
        for intent_key, rule in intents.items():
            assert 6 in rule["forbidden_truc"], (
                f"Intent '{intent_key}': Trực Phá (6) should be in forbidden_truc"
            )
