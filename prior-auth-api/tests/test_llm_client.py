"""LLM client boundary tests.

Covers: timeout, malformed JSON, invalid status, empty response, and
confirms that every failure path yields UNKNOWN — never SATISFIED.
"""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import Settings
from app.schemas.evaluation import CriterionEvaluation, CriterionSource
from app.schemas.triage import TriageRequest
from app.services.llm.llm_client import LLMClient


# ── Helpers ──────────────────────────────────────────────────────────────────

def _settings(enabled: bool = True) -> Settings:
    return Settings(llm_enabled=enabled, llm_provider="openai")


def _criterion() -> CriterionEvaluation:
    return CriterionEvaluation(
        criterion_id="C1",
        criterion="Documentation must demonstrate failed conservative treatment.",
        criterion_type="SEMANTIC",
        evaluator="LLM",
        status="UNKNOWN",
        source=CriterionSource(
            policy_type="LCD",
            policy_id="L99999",
            section="indications",
            extraction_method="STRUCTURED_FIELD",
        ),
    )


def _request() -> TriageRequest:
    return TriageRequest(
        procedure_code="64483",
        diagnosis_codes=["M54.16"],
        clinical_notes="Patient completed seven months of physical therapy with persistent pain.",
    )


def _call_client(raw_response: str) -> dict[str, Any]:
    """Run evaluate_criterion with a mocked _call_llm returning raw_response."""
    client = LLMClient(_settings())
    with patch.object(client, "_call_llm", return_value=raw_response):
        return client.evaluate_criterion(_criterion(), _request(), "Policy requires failed conservative treatment.")


# ── Tests ────────────────────────────────────────────────────────────────────

class TestValidResponse:
    def test_satisfied(self):
        raw = json.dumps({"status": "SATISFIED", "patient_evidence": ["Seven months of PT with persistent pain."]})
        result = _call_client(raw)
        assert result["status"] == "SATISFIED"
        assert result["patient_evidence"] != []

    def test_not_satisfied(self):
        raw = json.dumps({"status": "NOT_SATISFIED", "patient_evidence": []})
        result = _call_client(raw)
        assert result["status"] == "NOT_SATISFIED"

    def test_unknown(self):
        raw = json.dumps({"status": "UNKNOWN", "patient_evidence": []})
        result = _call_client(raw)
        assert result["status"] == "UNKNOWN"


class TestInvalidLLMOutput:
    def test_malformed_json_yields_unknown(self):
        """A response that is not valid JSON must produce UNKNOWN."""
        raw = "Sorry, I cannot evaluate that criterion."
        result = _call_client(raw)
        assert result["status"] == "UNKNOWN"

    def test_invalid_status_value_yields_unknown(self):
        """An unrecognised status string must be normalised to UNKNOWN."""
        raw = json.dumps({"status": "APPROVE", "patient_evidence": []})
        result = _call_client(raw)
        assert result["status"] == "UNKNOWN"

    def test_missing_status_field_yields_unknown(self):
        """JSON that is valid but lacks the 'status' key must produce UNKNOWN."""
        raw = json.dumps({"patient_evidence": ["Some evidence."]})
        result = _call_client(raw)
        assert result["status"] == "UNKNOWN"

    def test_empty_string_response_yields_unknown(self):
        raw = ""
        result = _call_client(raw)
        assert result["status"] == "UNKNOWN"

    def test_empty_json_object_yields_unknown(self):
        raw = "{}"
        result = _call_client(raw)
        assert result["status"] == "UNKNOWN"

    def test_markdown_wrapped_json_is_parsed(self):
        """JSON wrapped in a markdown code fence must still be parsed correctly."""
        raw = '```json\n{"status": "SATISFIED", "patient_evidence": ["PT completed."]}\n```'
        result = _call_client(raw)
        assert result["status"] == "SATISFIED"

    def test_status_case_normalised(self):
        """Lowercase 'satisfied' must be normalised to 'SATISFIED'."""
        raw = json.dumps({"status": "satisfied", "patient_evidence": []})
        result = _call_client(raw)
        assert result["status"] == "SATISFIED"


class TestLLMCallFailure:
    def test_exception_from_call_yields_unknown(self):
        """If _call_llm raises any exception, result must be UNKNOWN."""
        client = LLMClient(_settings())
        with patch.object(client, "_call_llm", side_effect=RuntimeError("Connection refused")):
            result = client.evaluate_criterion(_criterion(), _request(), "context")
        assert result["status"] == "UNKNOWN"

    def test_timeout_yields_unknown(self):
        """A timeout must produce UNKNOWN, never SATISFIED."""
        import openai
        client = LLMClient(_settings())
        with patch.object(client, "_call_llm", side_effect=openai.APITimeoutError(request=MagicMock())):
            result = client.evaluate_criterion(_criterion(), _request(), "context")
        assert result["status"] == "UNKNOWN"

    def test_network_error_yields_unknown(self):
        """Any network-level error must produce UNKNOWN."""
        import openai
        client = LLMClient(_settings())
        with patch.object(client, "_call_llm", side_effect=openai.APIConnectionError(request=MagicMock())):
            result = client.evaluate_criterion(_criterion(), _request(), "context")
        assert result["status"] == "UNKNOWN"

    def test_unknown_is_never_satisfied_on_failure(self):
        """Regression: no failure path may default to SATISFIED."""
        client = LLMClient(_settings())
        for exc in [RuntimeError("err"), ValueError("err"), Exception("err")]:
            with patch.object(client, "_call_llm", side_effect=exc):
                result = client.evaluate_criterion(_criterion(), _request(), "context")
            assert result["status"] != "SATISFIED", f"Got SATISFIED on {exc}"


class TestTimeout:
    def test_timeout_setting_propagated(self):
        """llm_timeout_seconds from Settings must be stored on the client."""
        settings = Settings(llm_enabled=True, llm_timeout_seconds=10)
        client = LLMClient(settings)
        assert client._timeout == 10

    def test_default_timeout_is_30(self):
        client = LLMClient(Settings(llm_enabled=True))
        assert client._timeout == 30
