import re
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.models import Customer
from app.services.embedding_service import OpenAIConfigurationError, OpenAIServiceError
from app.services.rag_service import answer_question, normalize_language
from app.services.report_service import build_weekly_risk_report, get_priority_customers
from app.services.risk_scoring_service import analyze_customer_risk


class AgentState(TypedDict, total=False):
    question: str
    language: str
    selected_tool: str
    answer: str
    reasoning_summary: str
    confidence: float
    data: dict[str, Any]
    sources: list[dict[str, Any]]
    actions: list[str]
    db: Session


def analyze_with_agent(db: Session, question: str, language: str = "en") -> dict[str, Any]:
    language = normalize_language(language)
    workflow = StateGraph(AgentState)
    workflow.add_node("route", _route_question)
    workflow.add_node("execute", _execute_selected_tool)
    workflow.set_entry_point("route")
    workflow.add_edge("route", "execute")
    workflow.add_edge("execute", END)
    graph = workflow.compile()
    result = graph.invoke({"db": db, "question": question, "language": language})

    return {
        "answer": result.get("answer", ""),
        "selected_tool": result.get("selected_tool", "fallback"),
        "reasoning_summary": result.get("reasoning_summary", ""),
        "confidence": result.get("confidence", 0.0),
        "data": result.get("data", {}),
        "sources": result.get("sources", []),
        "actions": result.get("actions", []),
        "language": language,
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
    language = normalize_language(state.get("language"))

    if selected_tool == "analyze_customer":
        return _run_customer_analysis(state, db, question, language)
    if selected_tool == "priority_customers":
        return _run_priority_customers(state, db, language)
    if selected_tool == "weekly_report":
        return _run_weekly_report(state, db, language)
    if selected_tool == "rag":
        return _run_rag(state, db, question, language)

    fallback_answer = {
        "en": (
            "I can analyze a customer, list priority customers, generate the weekly risk "
            "report or query processed documents."
        ),
        "fr": (
            "Je peux analyser un client, lister les clients prioritaires, generer le rapport "
            "hebdomadaire ou interroger les documents traites."
        ),
    }
    fallback_actions = {
        "en": [
            "Ask for high-risk customers this week.",
            "Ask to analyze a customer such as CUST-001.",
            "Ask a document question after processing a PDF or CSV.",
        ],
        "fr": [
            "Demander les clients a risque eleve cette semaine.",
            "Demander l'analyse d'un client comme CUST-001.",
            "Poser une question documentaire apres traitement d'un PDF ou CSV.",
        ],
    }
    return {
        **state,
        "answer": fallback_answer[language],
        "reasoning_summary": _reasoning("fallback", language),
        "confidence": 0.35,
        "data": {},
        "sources": [],
        "actions": fallback_actions[language],
    }


def _run_customer_analysis(
    state: AgentState,
    db: Session,
    question: str,
    language: str,
) -> AgentState:
    customer_id = _extract_customer_id(question)
    customer = (
        db.query(Customer)
        .filter(Customer.customer_external_id == customer_id)
        .one_or_none()
    )
    if customer is None:
        answer = (
            f"Customer {customer_id} was not found."
            if language == "en"
            else f"Client {customer_id} introuvable."
        )
        return {
            **state,
            "answer": answer,
            "reasoning_summary": _reasoning("analyze_customer", language),
            "confidence": 0.4,
            "data": {"customer_id": customer_id},
            "sources": [],
            "actions": _generic_actions(language),
        }

    analysis = analyze_customer_risk(db, customer)
    data = analysis.__dict__
    if language == "en":
        answer = (
            f"{analysis.customer_id} is {analysis.risk_level} risk "
            f"with a score of {analysis.risk_score}/100."
        )
    else:
        answer = (
            f"{analysis.customer_id} est en risque {analysis.risk_level} "
            f"avec un score de {analysis.risk_score}/100."
        )
    return {
        **state,
        "answer": answer,
        "reasoning_summary": _reasoning("analyze_customer", language),
        "confidence": 0.86,
        "data": data,
        "sources": [],
        "actions": _actions_from_analysis(data, language),
    }


def _run_priority_customers(state: AgentState, db: Session, language: str) -> AgentState:
    customers = get_priority_customers(db, limit=5)
    data = {"customers": [customer.model_dump() for customer in customers]}
    if not customers:
        answer = "No imported customer is available yet." if language == "en" else "Aucun client importe pour le moment."
        actions = _generic_actions(language)
        confidence = 0.3
    else:
        if language == "en":
            answer = (
                f"{len(customers)} priority customers identified. "
                f"The most urgent is {customers[0].customer_id} "
                f"with a score of {customers[0].risk_score}/100."
            )
        else:
            answer = (
                f"{len(customers)} clients prioritaires identifies. "
                f"Le plus urgent est {customers[0].customer_id} "
                f"avec un score de {customers[0].risk_score}/100."
            )
        actions = _actions_from_priority(customers, language)
        confidence = 0.88
    return {
        **state,
        "answer": answer,
        "reasoning_summary": _reasoning("priority_customers", language),
        "confidence": confidence,
        "data": data,
        "sources": [],
        "actions": actions,
    }


def _run_weekly_report(state: AgentState, db: Session, language: str) -> AgentState:
    report = build_weekly_risk_report(db)
    return {
        **state,
        "answer": report.executive_summary,
        "reasoning_summary": _reasoning("weekly_report", language),
        "confidence": 0.84,
        "data": report.model_dump(),
        "sources": [],
        "actions": report.recommended_actions or _generic_actions(language),
    }


def _run_rag(state: AgentState, db: Session, question: str, language: str) -> AgentState:
    try:
        result = answer_question(db=db, question=question, language=language)
    except (OpenAIConfigurationError, OpenAIServiceError) as exc:
        answer = (
            f"Document intelligence is unavailable: {exc}"
            if language == "en"
            else f"Intelligence documentaire indisponible : {exc}"
        )
        return {
            **state,
            "answer": answer,
            "reasoning_summary": _reasoning("rag", language),
            "confidence": 0.2,
            "data": {},
            "sources": [],
            "actions": _generic_actions(language),
        }

    return {
        **state,
        "answer": result.answer,
        "reasoning_summary": result.reasoning_summary,
        "confidence": result.confidence,
        "data": {},
        "sources": [source.model_dump() for source in result.sources],
        "actions": result.actions or [],
    }


def _reasoning(tool: str, language: str) -> str:
    labels = {
        "en": {
            "fallback": "The agent could not map the question to a specific operational tool.",
            "analyze_customer": "The agent detected a customer identifier and used the customer risk analysis tool.",
            "priority_customers": "The agent detected a risk prioritization request and used customer ranking data.",
            "weekly_report": "The agent detected a weekly summary request and used the reporting tool.",
            "rag": "The agent detected a document question and used the RAG document tool.",
        },
        "fr": {
            "fallback": "L'agent n'a pas associe la question a un outil operationnel specifique.",
            "analyze_customer": "L'agent a detecte un identifiant client et utilise l'analyse de risque client.",
            "priority_customers": "L'agent a detecte une demande de priorisation du risque et utilise le classement client.",
            "weekly_report": "L'agent a detecte une demande de synthese hebdomadaire et utilise le reporting.",
            "rag": "L'agent a detecte une question documentaire et utilise l'outil RAG.",
        },
    }
    return labels[language].get(tool, labels[language]["fallback"])


def _generic_actions(language: str) -> list[str]:
    if language == "fr":
        return [
            "Importer les clients si la base est vide.",
            "Entrainer le modele si les scores ne sont pas disponibles.",
            "Traiter les documents avant les questions documentaires.",
        ]
    return [
        "Import customers if the database is empty.",
        "Train the model if risk scores are unavailable.",
        "Process documents before asking document questions.",
    ]


def _actions_from_analysis(data: dict[str, Any], language: str) -> list[str]:
    recommended_actions = data.get("recommended_actions")
    if isinstance(recommended_actions, list) and recommended_actions:
        return [str(action) for action in recommended_actions[:5]]
    return _generic_actions(language)


def _actions_from_priority(customers: list[Any], language: str) -> list[str]:
    actions = []
    for customer in customers:
        actions.extend(getattr(customer, "recommended_actions", None) or [])
    if actions:
        return [str(action) for action in dict.fromkeys(actions)][:5]
    return _generic_actions(language)


def _extract_customer_id(question: str) -> str | None:
    match = re.search(r"cust[-_\s]?\d+", question, flags=re.IGNORECASE)
    if not match:
        return None
    normalized = match.group(0).upper().replace("_", "-").replace(" ", "-")
    if not normalized.startswith("CUST-"):
        normalized = normalized.replace("CUST", "CUST-")
    return normalized
