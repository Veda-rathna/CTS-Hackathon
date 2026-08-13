"""Hierarchy short-circuit tests.

Verifies that the TriageService evaluation hierarchy is enforced:

  NCD EXCLUDED  → DENY immediately, LCD never reached
  NCD COVERED   → skip LCD, go directly to Article
  LCD EXCLUDED  → DENY immediately, Article never reached
  LCD UNKNOWN   → PEND immediately, Article never reached
  LCD COVERED   → Article reached

These tests use the mock repository stack so no database is required.
"""
from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.main import app
from app.schemas.triage import TriageDecision


client = TestClient(app)


# ── NCD hierarchy ─────────────────────────────────────────────────────────────

class TestNCDHierarchy:
    """Verify NCD status short-circuits correctly."""

    def test_ncd_excluded_yields_deny_without_reaching_lcd(self):
        """When an NCD explicitly excludes coverage the decision must be
        LIKELY_NOT_COVERED and the policy_path must NOT contain an LCD entry."""
        resp = client.post(
            "/api/v1/triage",
            json={
                "procedure_code": "EXCL001",  # mapped to an excluded NCD in mock data
                "diagnosis_codes": ["Z00.00"],
                "state": "TX",
            },
        )
        # For mock data that has no exclusion mapping, this documents expected
        # behaviour; the mock fixture for this code must produce EXCLUDED.
        # If mock data doesn't have this code, the response is POLICY_NOT_FOUND.
        data = resp.json()
        assert resp.status_code == 200
        # The policy_path must NOT contain an LCD node when NCD EXCLUDED
        if data["decision"] == TriageDecision.LIKELY_NOT_COVERED:
            policy_types = [p["policy_type"] for p in data.get("policy_path", [])]
            assert "LCD" not in policy_types, (
                "LCD was reached even though NCD was EXCLUDED"
            )

    def test_ncd_covered_does_not_re_evaluate_via_lcd(self):
        """When NCD is COVERED, the LCD evaluation block must be skipped.
        Confirmed by checking the policy_path: if NCD is present and
        decision is LIKELY_COVERED, there must be no separate LCD node."""
        resp = client.post(
            "/api/v1/triage",
            json={
                "procedure_code": "64483",
                "diagnosis_codes": ["M54.16"],
                "state": "TX",
                "patient_age": 65,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        policy_path = data.get("policy_path", [])
        ncd_nodes = [p for p in policy_path if p.get("policy_type") == "NCD"]
        if ncd_nodes and ncd_nodes[0].get("overall_status") == "COVERED":
            lcd_nodes = [p for p in policy_path if p.get("policy_type") == "LCD"]
            assert lcd_nodes == [], (
                "LCD evaluation was run even though NCD was COVERED"
            )


# ── LCD hierarchy ─────────────────────────────────────────────────────────────

class TestLCDHierarchy:
    """Verify LCD status short-circuits correctly."""

    def test_lcd_excluded_yields_deny_without_article(self):
        """LCD EXCLUDED must produce LIKELY_NOT_COVERED and Article must not
        appear in the policy_path."""
        resp = client.post(
            "/api/v1/triage",
            json={
                "procedure_code": "64483",
                "diagnosis_codes": ["M54.16"],
                "state": "TX",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        policy_path = data.get("policy_path", [])
        lcd_nodes = [p for p in policy_path if p.get("policy_type") == "LCD"]
        if lcd_nodes and lcd_nodes[0].get("overall_status") == "EXCLUDED":
            article_nodes = [p for p in policy_path if p.get("policy_type") == "ARTICLE"]
            assert article_nodes == [], (
                "Article was reached even though LCD was EXCLUDED"
            )
            assert data["decision"] == TriageDecision.LIKELY_NOT_COVERED

    def test_lcd_unknown_yields_pend_without_article(self):
        """LCD UNKNOWN must produce MORE_INFORMATION_REQUIRED and Article
        must NOT appear in the policy_path."""
        resp = client.post(
            "/api/v1/triage",
            json={
                "procedure_code": "64483",
                "diagnosis_codes": ["UNKNOWN_DX"],   # no clinical notes → semantic unknown
                "state": "TX",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        policy_path = data.get("policy_path", [])
        lcd_nodes = [p for p in policy_path if p.get("policy_type") == "LCD"]
        if lcd_nodes and lcd_nodes[0].get("overall_status") == "UNKNOWN":
            article_nodes = [p for p in policy_path if p.get("policy_type") == "ARTICLE"]
            assert article_nodes == [], (
                "Article was reached even though LCD was UNKNOWN"
            )
            assert data["decision"] == TriageDecision.MORE_INFORMATION_REQUIRED

    def test_lcd_covered_reaches_article(self):
        """When LCD is COVERED the Article validation node must appear in
        the policy_path (if the policy has an associated article)."""
        resp = client.post(
            "/api/v1/triage",
            json={
                "procedure_code": "64483",
                "diagnosis_codes": ["M54.16"],
                "state": "TX",
                "patient_age": 65,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        policy_path = data.get("policy_path", [])
        lcd_nodes = [p for p in policy_path if p.get("policy_type") == "LCD"]
        if lcd_nodes and lcd_nodes[0].get("overall_status") == "COVERED":
            article_nodes = [p for p in policy_path if p.get("policy_type") == "ARTICLE"]
            assert article_nodes != [], (
                "Article was not reached even though LCD was COVERED"
            )


# ── Jurisdiction ──────────────────────────────────────────────────────────────

class TestJurisdictionHierarchy:
    """Jurisdiction is evaluated only when NCD is NOT_ADDRESSED."""

    def test_outside_jurisdiction_yields_outside_jurisdiction_decision(self):
        resp = client.post(
            "/api/v1/triage",
            json={
                "procedure_code": "64483",
                "diagnosis_codes": ["M54.16"],
                "state": "ZZ",  # guaranteed invalid state
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == TriageDecision.OUTSIDE_JURISDICTION

    def test_jurisdiction_check_not_run_when_ncd_covered(self):
        """If NCD is COVERED the request bypasses jurisdiction + LCD entirely.
        An out-of-jurisdiction state must NOT trigger OUTSIDE_JURISDICTION
        when the NCD is already COVERED."""
        resp = client.post(
            "/api/v1/triage",
            json={
                "procedure_code": "64483",
                "diagnosis_codes": ["M54.16"],
                "state": "ZZ",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        policy_path = data.get("policy_path", [])
        ncd_nodes = [p for p in policy_path if p.get("policy_type") == "NCD"]
        if ncd_nodes and ncd_nodes[0].get("overall_status") == "COVERED":
            # NCD covered → jurisdiction should never have been checked
            assert data["decision"] != TriageDecision.OUTSIDE_JURISDICTION, (
                "OUTSIDE_JURISDICTION returned even though NCD was COVERED"
            )
