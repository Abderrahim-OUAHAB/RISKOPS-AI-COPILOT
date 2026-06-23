import re
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.models import Customer
from app.services.embedding_service import OpenAIConfigurationError, OpenAIServiceError
from app.services.rag_service import answer_question
from app.services.report_service import build_weekly_risk_report, get_priority_customers
from app.services.risk_scoring_service import analyze_customer_risk


class AgentState(TypedDict, total=False):
    question: str
    selected_tool: str
    answer: str
    data: dict[str, Any]
    sources: list[dict[str, Any]]
    db: Session


def analyze_with_agent(db: Session, question: str) -> dict[str, Any]:
    workflow = StateGraph(AgentState)
    workflow.add_node("route", _route_question)
    workflow.add_node("execute", _execute_selected_tool)
    workflow.set_entry_point("route")
    workflow.add_edge("route", "execute")
    workflow.add_edge("execute", END)
    graph = workflow.compile()
    result = graph.invoke({"db": db, "question": question})

    return {
        "answer": result.get("answer", ""),
        "selected_tool": result.get("selected_tool", "fallback"),
        "data": result.get("data", {}),
        "sources": result.get("sources", []),
    }


def _route_question(state: AgentState) -> AgentState:
    question = state["question"].lower()
    selected_tool = "fallback"

    if _extract_customer_id(question):
        selected_tool = "analyze_customer"
    elif any(word in question for word in ["rapport", "report", "hebdo", "weekly"]):
        selected_tool = "weekly_report"
    elif any(word in question for word in ["top", "priorit", "risque", "risk"]):
        selected_tool = "priority_customers"
    elif any(word in question for word in ["document", "contrat", "pdf", "source"]):
        selected_tool = "rag"

    return {**state, "selected_tool": selected_tool}


def _execute_selected_tool(state: AgentState) -> AgentState:
    db = state["db"]
    selected_tool = state["selected_tool"]
    question = state["question"]

    if selected_tool == "analyze_customer":
        return _run_customer_analysis(state, db, question)
    if selected_tool == "priority_customers":
        return _run_priority_customers(state, db)
    if selected_tool == "weekly_report":
        return _run_weekly_report(state, db)
    if selected_tool == "rag":
        return _run_rag(state, db, question)

    return {
        **state,
        "answer": (
            "Je peux analyser un client, lister les clients prioritaires, "
            "generer le rapport hebdomadaire ou interroger les documents traites."
        ),
        "data": {},
        "sources": [],
    }


def _run_customer_analysis(state: AgentState, db: Session, question: str) -> AgentState:
    customer_id = _extract_customer_id(question)
    customer = (
        db.query(Customer)
        .filter(Customer.customer_external_id == customer_id)
        .one_or_none()
    )
    if customer is None:
        return {
            **state,
            "answer": f"Client {customer_id} introuvable.",
            "data": {"customer_id": customer_id},
            "sources": [],
        }

    analysis = analyze_customer_risk(db, customer)
    data = analysis.__dict__
    return {
        **state,
        "answer": (
            f"{analysis.customer_id} est en risque {analysis.risk_level} "
            f"avec un score de {analysis.risk_score}/100."
        ),
        "data": data,
        "sources": [],
    }


def _run_priority_customers(state: AgentState, db: Session) -> AgentState:
    customers = get_priority_customers(db, limit=5)
    data = {"customers": [customer.model_dump() for customer in customers]}
    if not customers:
        answer = "Aucun client importe pour le moment."
    else:
        answer = (
            f"{len(customers)} clients prioritaires identifies. "
            f"Le plus urgent est {customers[0].customer_id} "
            f"avec un score de {customers[0].risk_score}/100."
        )
    return {**state, "answer": answer, "data": data, "sources": []}


def _run_weekly_report(state: AgentState, db: Session) -> AgentState:
    report = build_weekly_risk_report(db)
    return {
        **state,
        "answer": report.executive_summary,
        "data": report.model_dump(),
        "sources": [],
    }


def _run_rag(state: AgentState, db: Session, question: str) -> AgentState:
    try:
        result = answer_question(db=db, question=question)
    except (OpenAIConfigurationError, OpenAIServiceError) as exc:
        return {
            **state,
            "answer": f"RAG indisponible: {exc}",
            "data": {},
            "sources": [],
        }

    return {
        **state,
        "answer": result.answer,
        "data": {},
        "sources": [source.model_dump() for source in result.sources],
    }


def _extract_customer_id(question: str) -> str | None:
    match = re.search(r"cust[-_\s]?\d+", question, flags=re.IGNORECASE)
    if not match:
        return None
    normalized = match.group(0).upper().replace("_", "-").replace(" ", "-")
    if not normalized.startswith("CUST-"):
        normalized = normalized.replace("CUST", "CUST-")
    return normalized
