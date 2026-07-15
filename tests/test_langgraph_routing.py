import pytest

from app.services.riskops_agent import _route_question


@pytest.mark.parametrize(
    ("question", "expected_tool"),
    [
        ("Which customers are high risk?", "priority_customers"),
        ("Analyze cust 42", "analyze_customer"),
        ("Generate the weekly report", "weekly_report"),
        ("What does the uploaded PDF say?", "rag"),
        ("Hello there", "fallback"),
        ("", "fallback"),
    ],
)
def test_agent_routes_supported_and_fallback_questions(question, expected_tool):
    result = _route_question({"question": question, "language": "en"})

    assert result["selected_tool"] == expected_tool
