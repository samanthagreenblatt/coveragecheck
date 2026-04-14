"""Unit tests for benefit data loading and structure."""
import json
import pytest
from app.benefits import load_plan, get_plan_summary


def test_load_plan_returns_dict():
    plan = load_plan()
    assert isinstance(plan, dict)


def test_plan_has_required_top_level_keys():
    plan = load_plan()
    required = ["plan_name", "plan_type", "deductible", "out_of_pocket_max", "copays",
                "prescription_tiers", "covered_services", "prior_authorization", "network"]
    for key in required:
        assert key in plan, f"Missing key: {key}"


def test_deductible_values():
    plan = load_plan()
    assert plan["deductible"]["individual"] == 1500
    assert plan["deductible"]["family"] == 3000


def test_out_of_pocket_max_values():
    plan = load_plan()
    assert plan["out_of_pocket_max"]["individual"] == 5000
    assert plan["out_of_pocket_max"]["family"] == 10000


def test_copay_keys_present():
    plan = load_plan()
    expected_copays = [
        "primary_care", "specialist", "urgent_care", "emergency_room",
        "mental_health_therapy", "mental_health_psychiatry", "telehealth",
        "preventive_care", "lab_work", "physical_therapy"
    ]
    for key in expected_copays:
        assert key in plan["copays"], f"Missing copay: {key}"


def test_urgent_care_copay():
    plan = load_plan()
    assert plan["copays"]["urgent_care"]["amount"] == 75


def test_primary_care_copay():
    plan = load_plan()
    assert plan["copays"]["primary_care"]["amount"] == 25


def test_preventive_care_is_free():
    plan = load_plan()
    assert plan["copays"]["preventive_care"]["amount"] == 0


def test_mental_health_therapy_copay():
    plan = load_plan()
    assert plan["copays"]["mental_health_therapy"]["amount"] == 30


def test_telehealth_copay():
    plan = load_plan()
    assert plan["copays"]["telehealth"]["amount"] == 15


def test_prescription_tiers_present():
    plan = load_plan()
    tiers = plan["prescription_tiers"]
    assert "tier_1_generic" in tiers
    assert "tier_2_preferred_brand" in tiers
    assert "tier_3_non_preferred" in tiers
    assert "tier_4_specialty" in tiers
    assert "birth_control" in tiers


def test_generic_rx_copay():
    plan = load_plan()
    assert plan["prescription_tiers"]["tier_1_generic"]["copay"] == 10


def test_birth_control_is_free():
    plan = load_plan()
    assert plan["prescription_tiers"]["birth_control"]["copay"] == 0


def test_covered_services_includes_mental_health():
    plan = load_plan()
    assert plan["covered_services"]["mental_health"] is True


def test_dental_not_covered():
    plan = load_plan()
    assert plan["covered_services"]["dental"] is False


def test_gym_not_covered():
    plan = load_plan()
    assert plan["covered_services"]["gym_membership"] is False


def test_no_referral_required():
    plan = load_plan()
    assert plan["referral_required"] is False


def test_mri_requires_prior_auth():
    plan = load_plan()
    assert "MRI" in plan["prior_authorization"]["required_for"]


def test_primary_care_no_prior_auth():
    plan = load_plan()
    assert "primary_care" in plan["prior_authorization"]["not_required_for"]


def test_get_plan_summary_is_valid_json():
    summary = get_plan_summary()
    parsed = json.loads(summary)
    assert isinstance(parsed, dict)
    assert parsed["plan_type"] == "PPO"
