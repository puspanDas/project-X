"""
PhoneTracer — Comprehensive Test Suite
=======================================
Tests both the AI service (unit tests) and FastAPI endpoints (integration tests).
No running server needed — uses FastAPI TestClient for integration tests.

Usage:
    python -m pytest test_app.py -v           # Run all tests
    python -m pytest test_app.py -k unit      # Unit tests only
    python -m pytest test_app.py -k integration  # Integration tests only
"""

import sys
import os
import pytest

# Add backend to path so we can import ai_service directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))


# =========================================================================
# UNIT TESTS — AI Service (rule-based, no LLM needed)
# =========================================================================

class TestScoreSpamReports:
    """unit: _score_spam_reports thresholds."""

    def test_zero_reports(self):
        from ai_service import _score_spam_reports
        pts, factors = _score_spam_reports(0)
        assert pts == 0
        assert factors == []

    def test_one_report(self):
        from ai_service import _score_spam_reports
        pts, factors = _score_spam_reports(1)
        assert pts == 8
        assert len(factors) == 1

    def test_two_reports(self):
        from ai_service import _score_spam_reports
        pts, _ = _score_spam_reports(2)
        assert pts == 15

    def test_five_reports(self):
        from ai_service import _score_spam_reports
        pts, _ = _score_spam_reports(5)
        assert pts == 25

    def test_ten_plus_reports(self):
        from ai_service import _score_spam_reports
        pts, factors = _score_spam_reports(15)
        assert pts == 35
        assert "15" in factors[0]


class TestScoreLineType:
    """unit: _score_line_type lookups."""

    def test_voip(self):
        from ai_service import _score_line_type
        pts, factors = _score_line_type({"line_type": "VoIP"})
        assert pts == 15
        assert "VoIP" in factors[0]

    def test_premium_rate(self):
        from ai_service import _score_line_type
        pts, _ = _score_line_type({"line_type": "Premium Rate"})
        assert pts == 12

    def test_toll_free(self):
        from ai_service import _score_line_type
        pts, _ = _score_line_type({"line_type": "Toll-Free"})
        assert pts == 5

    def test_landline(self):
        from ai_service import _score_line_type
        pts, factors = _score_line_type({"line_type": "Landline"})
        assert pts == -3
        assert "lower risk" in factors[0]

    def test_mobile_no_score(self):
        from ai_service import _score_line_type
        pts, factors = _score_line_type({"line_type": "Mobile"})
        assert pts == 0
        assert factors == []

    def test_missing_line_type(self):
        from ai_service import _score_line_type
        pts, _ = _score_line_type({})
        assert pts == 0


class TestScoreCountry:
    """unit: _score_country risk tiers."""

    def test_high_risk(self):
        from ai_service import _score_country
        pts, factors = _score_country({"country_code": "NG", "country_name": "Nigeria"})
        assert pts == 15
        assert "high-risk" in factors[0]

    def test_medium_risk(self):
        from ai_service import _score_country
        pts, factors = _score_country({"country_code": "CN", "country_name": "China"})
        assert pts == 8
        assert "medium-risk" in factors[0]

    def test_normal_risk(self):
        from ai_service import _score_country
        pts, factors = _score_country({"country_code": "US", "country_name": "United States"})
        assert pts == 0
        assert "normal" in factors[0]


class TestScoreCarrier:
    """unit: _score_carrier checks."""

    def test_unknown_carrier(self):
        from ai_service import _score_carrier
        pts, _ = _score_carrier({"carrier": "Unknown"})
        assert pts == 10

    def test_empty_carrier(self):
        from ai_service import _score_carrier
        pts, _ = _score_carrier({"carrier": ""})
        assert pts == 10

    def test_virtual_carrier(self):
        from ai_service import _score_carrier
        pts, _ = _score_carrier({"carrier": "Virtual Telecom Inc"})
        assert pts == 8

    def test_normal_carrier(self):
        from ai_service import _score_carrier
        pts, _ = _score_carrier({"carrier": "Verizon"})
        assert pts == 0


class TestScoreValidity:
    """unit: _score_validity checks."""

    def test_invalid_number(self):
        from ai_service import _score_validity
        pts, _ = _score_validity({"valid": False})
        assert pts == 15

    def test_impossible_number(self):
        from ai_service import _score_validity
        pts, _ = _score_validity({"valid": True, "possible": False})
        assert pts == 10

    def test_valid_number(self):
        from ai_service import _score_validity
        pts, _ = _score_validity({"valid": True, "possible": True})
        assert pts == 0


class TestScorePorting:
    """unit: _score_porting checks."""

    def test_ported_number(self):
        from ai_service import _score_porting
        pts, factors = _score_porting({"original_carrier": "AT&T", "carrier": "Verizon"})
        assert pts == 5
        assert "ported" in factors[0]

    def test_not_ported(self):
        from ai_service import _score_porting
        pts, _ = _score_porting({"original_carrier": "AT&T", "carrier": "AT&T"})
        assert pts == 0


class TestScoreReportContents:
    """unit: _score_report_contents keyword detection."""

    def test_severe_keyword(self):
        from ai_service import _score_report_contents
        reports = [{"type": "fraud", "description": "Tried to get my bank account details"}]
        pts, factors = _score_report_contents(reports)
        assert pts >= 5  # 5 for keyword + up to 20 for type score
        assert any("bank" in f for f in factors)

    def test_moderate_keyword(self):
        from ai_service import _score_report_contents
        reports = [{"type": "spam", "description": "Automated spam recording"}]
        pts, _ = _score_report_contents(reports)
        assert pts >= 2  # at least 2 for moderate keyword

    def test_no_keywords(self):
        from ai_service import _score_report_contents
        reports = [{"type": "other", "description": "Just a test"}]
        pts, _ = _score_report_contents(reports)
        assert pts == 5  # only the type score for "other"

    def test_empty_reports(self):
        from ai_service import _score_report_contents
        pts, _ = _score_report_contents([])
        assert pts == 0


class TestDetermineRiskLevel:
    """unit: _determine_risk_level thresholds."""

    def test_critical(self):
        from ai_service import _determine_risk_level
        assert _determine_risk_level(70) == "Critical"
        assert _determine_risk_level(100) == "Critical"

    def test_high(self):
        from ai_service import _determine_risk_level
        assert _determine_risk_level(45) == "High"
        assert _determine_risk_level(69) == "High"

    def test_medium(self):
        from ai_service import _determine_risk_level
        assert _determine_risk_level(25) == "Medium"
        assert _determine_risk_level(44) == "Medium"

    def test_low(self):
        from ai_service import _determine_risk_level
        assert _determine_risk_level(0) == "Low"
        assert _determine_risk_level(24) == "Low"


class TestDetermineThreatType:
    """unit: _determine_threat_type classification."""

    def test_fraud(self):
        from ai_service import _determine_threat_type
        reports = [{"type": "fraud"}]
        assert _determine_threat_type({}, reports, 50) == "Fraud / Phishing"

    def test_phishing(self):
        from ai_service import _determine_threat_type
        reports = [{"type": "phishing"}]
        assert _determine_threat_type({}, reports, 50) == "Fraud / Phishing"

    def test_scam(self):
        from ai_service import _determine_threat_type
        reports = [{"type": "scam"}]
        assert _determine_threat_type({}, reports, 50) == "Scam"

    def test_harassment(self):
        from ai_service import _determine_threat_type
        reports = [{"type": "harassment"}]
        assert _determine_threat_type({}, reports, 30) == "Harassment"

    def test_telemarketing(self):
        from ai_service import _determine_threat_type
        reports = [{"type": "robocall"}]
        assert _determine_threat_type({}, reports, 20) == "Telemarketing"

    def test_spam(self):
        from ai_service import _determine_threat_type
        reports = [{"type": "spam"}]
        assert _determine_threat_type({}, reports, 10) == "Spam"

    def test_suspicious_voip(self):
        from ai_service import _determine_threat_type
        assert _determine_threat_type({"line_type": "VoIP"}, [], 35) == "Suspicious VoIP"

    def test_premium_rate(self):
        from ai_service import _determine_threat_type
        assert _determine_threat_type({"line_type": "Premium Rate"}, [], 10) == "Premium Rate"

    def test_clean(self):
        from ai_service import _determine_threat_type
        assert _determine_threat_type({"line_type": "Mobile"}, [], 10) == "Clean"


class TestGenerateRecommendation:
    """unit: _generate_recommendation returns correct text per level."""

    def test_critical(self):
        from ai_service import _generate_recommendation
        rec = _generate_recommendation("Critical", "Fraud", {})
        assert "Do NOT answer" in rec

    def test_high(self):
        from ai_service import _generate_recommendation
        rec = _generate_recommendation("High", "Scam", {})
        assert "extreme caution" in rec

    def test_medium(self):
        from ai_service import _generate_recommendation
        rec = _generate_recommendation("Medium", "Spam", {})
        assert "cautious" in rec.lower()

    def test_low(self):
        from ai_service import _generate_recommendation
        rec = _generate_recommendation("Low", "Clean", {})
        assert "appears safe" in rec


class TestGenerateAnalysis:
    """unit: _generate_analysis openers."""

    def test_critical_opener(self):
        from ai_service import _generate_analysis
        result = _generate_analysis(
            {"formatted_international": "+1234", "country_name": "US", "carrier": "AT&T", "line_type": "VoIP"},
            ["Factor 1"], "Critical", 80
        )
        assert "malicious" in result.lower()

    def test_low_opener(self):
        from ai_service import _generate_analysis
        result = _generate_analysis(
            {"formatted_international": "+1234", "country_name": "US", "carrier": "AT&T", "line_type": "Mobile"},
            [], "Low", 10
        )
        assert "safe" in result.lower()


class TestAnalyzeNumber:
    """unit: Full analyze_number pipeline (rule-based, LLM mocked out)."""

    def _make_trace(self, **overrides):
        base = {
            "formatted_international": "+1 415-858-6273",
            "number": "+14158586273",
            "e164": "+14158586273",
            "valid": True,
            "possible": True,
            "country_code": "US",
            "country_name": "United States",
            "carrier": "AT&T",
            "original_carrier": "AT&T",
            "line_type": "Mobile",
            "spam_reports": 0,
        }
        base.update(overrides)
        return base

    def test_clean_number(self):
        from ai_service import analyze_number
        result = analyze_number(self._make_trace(), [])
        assert result["risk_level"] == "Low"
        assert result["risk_score"] < 25
        assert result["threat_type"] == "Clean"
        assert result["ai_source"] in ("rule-based", "llm")

    def test_high_spam_critical(self):
        from ai_service import analyze_number
        trace = self._make_trace(spam_reports=12, line_type="VoIP", carrier="Unknown")
        reports = [{"type": "fraud", "description": "Tried to steal my bank account"}] * 3
        result = analyze_number(trace, reports)
        assert result["risk_level"] in ("Critical", "High")
        assert result["risk_score"] >= 45

    def test_voip_medium_risk(self):
        from ai_service import analyze_number
        trace = self._make_trace(line_type="VoIP", spam_reports=1)
        result = analyze_number(trace, [])
        assert result["risk_score"] >= 20  # VoIP (15) + 1 spam (8) = 23 minimum
        assert "VoIP" in str(result["factors"])

    def test_result_structure(self):
        from ai_service import analyze_number
        result = analyze_number(self._make_trace(), [])
        required_keys = {
            "risk_score", "risk_level", "threat_type", "factors",
            "analysis", "recommendation", "ai_source", "model", "analyzed_at",
        }
        assert required_keys.issubset(result.keys())

    def test_score_clamped_to_100(self):
        from ai_service import analyze_number
        trace = self._make_trace(
            spam_reports=20, valid=False, line_type="VoIP",
            country_code="NG", country_name="Nigeria",
            carrier="Unknown",
        )
        reports = [{"type": "fraud", "description": "bank password ssn bitcoin ransom"}] * 10
        result = analyze_number(trace, reports)
        assert result["risk_score"] <= 100


class TestChatKnowledgeBase:
    """unit: Chat knowledge-base fallback responses."""

    def test_greeting(self):
        from ai_service import chat
        result = chat("hello")
        assert result["ai_source"] in ("rule-based", "llm")
        assert "response" in result
        assert len(result["response"]) > 10

    def test_scam_question(self):
        from ai_service import chat
        result = chat("How can I identify a scam call?")
        assert "Scam" in result["response"]
        assert result["confidence"] > 0

    def test_voip_question(self):
        from ai_service import chat
        result = chat("What is a VoIP number?")
        assert "VoIP" in result["response"]

    def test_block_question(self):
        from ai_service import chat
        result = chat("How do I block unwanted calls?")
        assert "block" in result["response"].lower()

    def test_report_question(self):
        from ai_service import chat
        result = chat("How to report spam to FTC?")
        assert "Report" in result["response"]

    def test_unknown_topic(self):
        from ai_service import chat
        result = chat("Tell me about quantum mechanics")
        # LLM may respond with a redirect; rule-based gives default response
        assert "response" in result
        assert len(result["response"]) > 10

    def test_result_structure(self):
        from ai_service import chat
        result = chat("hi")
        required_keys = {"response", "confidence", "ai_source", "model", "timestamp"}
        assert required_keys.issubset(result.keys())


class TestMatchKnowledgeBase:
    """unit: _match_knowledge_base pattern scoring."""

    def test_exact_pattern_match(self):
        from ai_service import _match_knowledge_base
        response, confidence = _match_knowledge_base("hello")
        assert "Phone Safety" in response
        assert confidence > 0

    def test_no_match(self):
        from ai_service import _match_knowledge_base
        response, confidence = _match_knowledge_base("xyzzyqwrt")
        assert confidence == 0


# =========================================================================
# INTEGRATION TESTS — FastAPI endpoints via TestClient
# =========================================================================

@pytest.fixture(scope="module")
def client():
    """Create a TestClient for the FastAPI app (no server needed)."""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


class TestIntegrationHealth:
    """integration: Health check endpoint."""

    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestIntegrationTrace:
    """integration: Phone number trace endpoint."""

    def test_trace_valid_number(self, client):
        resp = client.get("/api/trace", params={"number": "+14158586273"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["country_code"] == "US"
        assert "carrier" in data
        assert "line_type" in data

    def test_trace_invalid_format(self, client):
        resp = client.get("/api/trace", params={"number": "not-a-number"})
        assert resp.status_code == 400

    def test_trace_indian_number(self, client):
        resp = client.get("/api/trace", params={"number": "+919876543210"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["country_code"] == "IN"


class TestIntegrationAIAnalyze:
    """integration: AI analysis endpoint."""

    def test_analyze(self, client):
        trace_data = {
            "formatted_international": "+1 415-858-6273",
            "e164": "+14158586273",
            "valid": True,
            "possible": True,
            "country_code": "US",
            "country_name": "United States",
            "carrier": "AT&T",
            "original_carrier": "AT&T",
            "line_type": "Mobile",
            "spam_reports": 0,
        }
        resp = client.post("/api/ai/analyze", json={"trace_data": trace_data})
        assert resp.status_code == 200
        data = resp.json()
        assert "risk_score" in data
        assert "risk_level" in data
        assert data["risk_level"] in ("Low", "Medium", "High", "Critical")


class TestIntegrationAIChat:
    """integration: AI chatbot endpoint."""

    def test_chat(self, client):
        resp = client.post("/api/ai/chat", json={"message": "hello", "history": []})
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert len(data["response"]) > 0

    def test_chat_safety_question(self, client):
        resp = client.post("/api/ai/chat", json={"message": "How to block spam calls?", "history": []})
        assert resp.status_code == 200
        data = resp.json()
        assert "Block" in data["response"]


class TestIntegrationAIStatus:
    """integration: AI model status endpoint."""

    def test_status(self, client):
        resp = client.get("/api/ai/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "state" in data


class TestIntegrationReport:
    """integration: Report submission endpoint."""

    def test_report_valid(self, client):
        resp = client.post("/api/report", json={
            "number": "+14158586273",
            "type": "spam",
            "description": "Test spam report",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data

    def test_report_invalid_number(self, client):
        resp = client.post("/api/report", json={
            "number": "invalid",
            "type": "spam",
            "description": "Test",
        })
        assert resp.status_code == 400


class TestIntegrationRecent:
    """integration: Recent lookups endpoint."""

    def test_recent(self, client):
        resp = client.get("/api/recent")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
