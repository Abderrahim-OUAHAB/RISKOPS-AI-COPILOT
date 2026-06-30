import html
from typing import Any

import pandas as pd
import streamlit as st

from api_client import (
    analyze_agent,
    analyze_customer_risk,
    ask_rag,
    complete_action,
    explain_customer_risk,
    get_action_plan,
    get_actions,
    get_action_board,
    get_client_360,
    get_customers,
    get_document_risk,
    get_documents,
    get_health,
    get_llm_summary,
    get_llm_traces,
    get_ml_report_status,
    get_priority_customers,
    get_ready,
    get_risk_history,
    get_weekly_report,
    safe_post,
    sync_recommended_actions,
)
from components import (
    format_list_items,
    inject_global_css,
    metric_card,
    render_empty_state,
    render_error,
    render_risk_score,
    render_success,
    render_warning,
    risk_badge,
    risk_color,
    safe_json_preview,
    section_header,
    status_badge,
)
from translations import LANGUAGE_OPTIONS, translate


PAGE_KEYS = [
    "executive_overview",
    "client_risk",
    "action_board",
    "documents_rag",
    "ai_assistant",
    "data_pipeline",
    "monitoring",
    "about_project",
]
APP_VERSION = "v1.2.1"
PIPELINE_TASKS = [
    "health_check_api",
    "import_sample_customers",
    "run_dbt_models",
    "run_dbt_tests",
    "train_churn_model",
    "generate_weekly_risk_report",
    "pipeline_summary",
]


st.set_page_config(
    page_title="AI RiskOps Copilot",
    page_icon="",
    layout="wide",
)
inject_global_css()


def current_language() -> str:
    return st.session_state.get("language", "en")


def t(key: str, **kwargs: Any) -> str:
    text = translate(key, current_language())
    return text.format(**kwargs) if kwargs else text


def _status_label(status: str | None) -> str:
    key = str(status or "").strip().lower()
    labels = {
        "ok": t("healthy"),
        "healthy": t("healthy"),
        "ready": t("ready"),
        "success": t("ready"),
        "processed": t("processed"),
        "warning": t("warning"),
        "degraded": t("warning"),
        "uploaded": t("needs_processing"),
        "pending": t("needs_processing"),
        "error": t("error"),
        "failed": t("error"),
        "processing_failed": t("error"),
        "unavailable": t("unavailable"),
        "not_ready": t("not_ready"),
    }
    return labels.get(key, str(status or "unknown").replace("_", " ").title())


def _risk_label(level: str | None) -> str:
    key = str(level or "").strip().lower()
    if current_language() == "fr":
        return {
            "high": "Élevé",
            "medium": "Moyen",
            "low": "Faible",
        }.get(key, str(level or "Inconnu").title())
    return str(level or "unknown").title()


def _pipeline_task_label(task: str) -> str:
    labels = {
        "en": {
            "health_check_api": "API health check",
            "import_sample_customers": "Customer data import",
            "run_dbt_models": "dbt model build",
            "run_dbt_tests": "dbt quality tests",
            "train_churn_model": "Churn model training",
            "generate_weekly_risk_report": "Weekly risk report",
            "pipeline_summary": "Pipeline summary",
        },
        "fr": {
            "health_check_api": "Contrôle santé API",
            "import_sample_customers": "Import des données client",
            "run_dbt_models": "Build des modèles dbt",
            "run_dbt_tests": "Tests qualité dbt",
            "train_churn_model": "Entraînement du modèle churn",
            "generate_weekly_risk_report": "Rapport hebdomadaire des risques",
            "pipeline_summary": "Synthèse du pipeline",
        },
    }
    return labels.get(current_language(), labels["en"]).get(task, task.replace("_", " ").title())


def render_product_header() -> None:
    st.markdown(
        f"""
        <div class="riskops-product-header">
            <h1>AI RiskOps Copilot</h1>
            <p>{html.escape(t("header_subtitle"))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("## AI RiskOps Copilot")
        st.caption(t("product_tagline"))

        language_codes = list(LANGUAGE_OPTIONS.keys())
        current_code = current_language()
        previous_language = current_code
        selected_language = st.selectbox(
            t("language"),
            language_codes,
            index=language_codes.index(current_code) if current_code in language_codes else 0,
            format_func=lambda code: LANGUAGE_OPTIONS[code],
        )
        st.session_state["language"] = selected_language
        previous_default_question = translate("default_agent_question", previous_language)
        if (
            previous_language != selected_language
            and st.session_state.get("agent_question") == previous_default_question
        ):
            st.session_state["agent_question"] = translate("default_agent_question", selected_language)
        st.markdown(status_badge("ready", t("secure_workspace")), unsafe_allow_html=True)
        st.caption(t("version"))

        page = st.radio(
            t("navigation"),
            PAGE_KEYS,
            label_visibility="collapsed",
            format_func=lambda page_key: t(f"page.{page_key}"),
        )

        st.divider()
        st.markdown(f"### {t('system_status')}")
        health = get_health()
        if health.ok:
            st.markdown(status_badge("healthy", t("healthy")), unsafe_allow_html=True)
        else:
            st.markdown(status_badge("unavailable", t("unavailable")), unsafe_allow_html=True)
            st.caption(health.error)

        st.divider()
        st.markdown(f"### {t('platform_links')}")
        st.link_button(t("api_documentation"), "http://localhost:8000/docs", use_container_width=True)
        st.link_button(t("workflow_orchestration"), "http://localhost:8080", use_container_width=True)
        st.link_button(
            t("ml_monitoring_report"),
            "http://localhost:8000/monitoring/ml/report?format=html",
            use_container_width=True,
        )

    return page


def _customers() -> list[dict]:
    result = get_customers()
    if not result.ok:
        render_warning(f"{t('customer_records')} unavailable: {result.error}")
        return []
    return result.data or []


def _customer_options(customers: list[dict]) -> dict[str, str]:
    return {
        f"{customer.get('customer_external_id')} - {customer.get('name') or t('customer_record')}": customer.get(
            "customer_external_id"
        )
        for customer in customers
        if customer.get("customer_external_id")
    }


def _risk_table(customers: list[dict]) -> None:
    if not customers:
        render_empty_state(t("import_customer_data"))
        return

    rows = [
        {
            t("customer"): customer.get("customer_id") or customer.get("customer_external_id"),
            t("name"): customer.get("name"),
            t("risk_score"): customer.get("risk_score"),
            t("level"): _risk_label(customer.get("risk_level")),
            t("support_tickets"): customer.get("support_tickets"),
            t("late_payments"): customer.get("late_payments"),
        }
        for customer in customers
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_percent(value: Any) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "-"


def _customer_name(customer: dict) -> str:
    return str(customer.get("name") or t("customer_record"))


def _customer_external_id(customer: dict) -> str:
    return str(customer.get("customer_id") or customer.get("customer_external_id") or "")


def _dedupe(items: list[str], limit: int | None = None) -> list[str]:
    seen = set()
    output = []
    for item in items:
        clean_item = str(item).strip()
        if not clean_item or clean_item.lower() in seen:
            continue
        seen.add(clean_item.lower())
        output.append(clean_item)
        if limit is not None and len(output) >= limit:
            break
    return output


def _recommended_actions(priority_rows: list[dict], weekly_report: dict, limit: int = 5) -> list[str]:
    actions: list[str] = []
    for customer in priority_rows:
        if str(customer.get("risk_level", "")).lower() == "high":
            actions.extend(customer.get("recommended_actions") or [])
    actions.extend(weekly_report.get("recommended_actions") or [])
    fallback_actions = [
        "Contact high-risk customers within 48 hours"
        if current_language() == "en"
        else "Contacter les clients à risque élevé sous 48 heures",
        "Review late payments"
        if current_language() == "en"
        else "Revoir les retards de paiement",
        "Escalate repeated support issues"
        if current_language() == "en"
        else "Escalader les problèmes support répétés",
        "Prepare retention offer"
        if current_language() == "en"
        else "Préparer une offre de rétention",
        "Monitor medium-risk customers this week"
        if current_language() == "en"
        else "Surveiller les clients à risque moyen cette semaine",
    ]
    return _dedupe(actions + fallback_actions, limit=limit)


def _main_risk_drivers(priority_rows: list[dict]) -> list[str]:
    reasons: list[str] = []
    for customer in priority_rows:
        reasons.extend(customer.get("top_reasons") or [])
    if not reasons:
        if current_language() == "fr":
            return ["Retards de paiement", "Tickets support répétés", "Probabilité de churn élevée"]
        return ["Late payments", "Repeated support tickets", "High churn probability"]
    return _dedupe(reasons, limit=4)


def _business_summary(customers: list[dict], priority_rows: list[dict], weekly_report: dict) -> str:
    total_attention = _as_int(weekly_report.get("high_risk_customers")) + _as_int(
        weekly_report.get("medium_risk_customers")
    )
    if not total_attention and priority_rows:
        total_attention = len(priority_rows)
    total_customers = _as_int(weekly_report.get("total_customers"), len(customers))
    drivers = ", ".join(driver.lower() for driver in _main_risk_drivers(priority_rows)[:3])
    if total_customers == 0:
        return t("no_customers")
    return t("attention_summary", count=total_attention, drivers=drivers)


def _render_insight(title: str, body: str, color: str = "#2563EB") -> None:
    st.markdown(
        f"""
        <div class="riskops-insight-box" style="border-left-color:{html.escape(color)};">
            <div class="riskops-insight-title">{html.escape(title)}</div>
            <div class="riskops-insight-body">{html.escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_action_checklist(actions: list[str]) -> None:
    if not actions:
        render_empty_state(t("no_items"))
        return
    items = "".join(
        f'<li><span class="riskops-check">&#10003;</span>{html.escape(action)}</li>'
        for action in actions
    )
    st.markdown(f'<ul class="riskops-checklist">{items}</ul>', unsafe_allow_html=True)


def _format_confidence(confidence: Any) -> str:
    try:
        return f"{float(confidence) * 100:.0f}%"
    except (TypeError, ValueError):
        return "0%"


def _render_structured_response(data: dict[str, Any]) -> None:
    confidence = data.get("confidence")
    if confidence is not None:
        metric_card(t("confidence"), _format_confidence(confidence), t("response_mode"), "#2563EB")

    reasoning_summary = data.get("reasoning_summary")
    if reasoning_summary:
        _render_insight(t("reasoning_summary"), str(reasoning_summary), "#0F766E")

    actions = data.get("actions") or []
    if actions:
        st.markdown(f"#### {t('actions')}")
        _render_action_checklist([str(action) for action in actions])

    missing_information = data.get("missing_information") or []
    if missing_information:
        st.markdown(f"#### {t('missing_information')}")
        st.markdown(format_list_items([str(item) for item in missing_information], t("no_items")), unsafe_allow_html=True)


def _render_sources(sources: list[dict[str, Any]]) -> None:
    if not sources:
        render_empty_state(t("no_sources"))
        return

    st.markdown(f"#### {t('sources')}")
    for index, source in enumerate(sources, start=1):
        score = source.get("similarity_score")
        filename = source.get("document_name") or source.get("filename") or source.get("document_id")
        chunk_label = source.get("chunk_index")
        title = (
            f"{index}. {filename} | chunk {chunk_label} | "
            f"{t('similarity')}: {score}"
        )
        with st.expander(title):
            st.caption(
                f"{t('source_document')}: {filename} | "
                f"{t('type')}: {source.get('document_type') or '-'} | "
                f"chunk_id: {source.get('chunk_id')}"
            )
            st.write(source.get("content_preview") or source)


def _breakdown_label(key: str) -> str:
    labels = {
        "ml": t("ml_risk"),
        "payment": t("payment_risk"),
        "support": t("support_risk"),
        "contract": t("contract_risk"),
        "document": t("document_risk"),
        "trend": t("trend_risk"),
        "recency": t("recency_weighting"),
    }
    return labels.get(key, key.replace("_", " ").title())


def _render_score_breakdown(analysis: dict[str, Any]) -> None:
    breakdown = analysis.get("score_breakdown") or {}
    weighted = analysis.get("weighted_score_breakdown") or {}
    if not breakdown:
        render_empty_state(t("no_items"))
        return

    rows = [
        {
            t("risk_factor"): _breakdown_label(key),
            t("signal_score"): breakdown.get(key, 0),
            t("weighted_points"): weighted.get(key, 0),
        }
        for key in ["ml", "payment", "support", "contract", "document", "trend", "recency"]
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_document_risk(document_risk: dict[str, Any]) -> None:
    score = document_risk.get("document_risk_score", 0)
    level = document_risk.get("document_risk_level", "low")
    col1, col2 = st.columns([1, 2])
    with col1:
        render_risk_score(score, level, t("document_risk_score"), _risk_label(level))
    with col2:
        signals = document_risk.get("document_risk_signals") or []
        if signals:
            _render_insight(t("document_signals"), ", ".join(signals), risk_color(level))
        else:
            render_empty_state(t("no_document_risk_detected"))

    linked_documents = document_risk.get("linked_documents") or []
    st.markdown(f"#### {t('linked_documents')}")
    if linked_documents:
        doc_rows = [
            {
                t("documents"): doc.get("filename"),
                t("type"): doc.get("document_type"),
                t("status"): doc.get("status"),
            }
            for doc in linked_documents
        ]
        st.dataframe(pd.DataFrame(doc_rows), use_container_width=True, hide_index=True)
    else:
        render_empty_state(t("no_linked_documents"))


def _render_document_evidence(evidence: list[dict[str, Any]]) -> None:
    st.markdown(f"#### {t('evidence_from_documents')}")
    if not evidence:
        render_empty_state(t("no_document_risk_detected"))
        return

    for item in evidence[:5]:
        title = f"{item.get('signal')} | {item.get('filename')} | chunk {item.get('chunk_index', '-')}"
        with st.expander(title):
            st.caption(", ".join(item.get("matched_keywords") or []))
            st.write(item.get("content_preview"))


def _render_action_plan_table(actions: list[dict[str, Any]]) -> None:
    if not actions:
        render_empty_state(t("no_items"))
        return

    headers = [t("customer"), t("priority"), t("action"), t("owner"), t("due_date"), t("reason")]
    rows = []
    for action in actions[:5]:
        rows.append(
            [
                str(action.get("customer_name") or action.get("customer_id") or "-"),
                str(action.get("priority") or "-"),
                str(action.get("action_label") or "-"),
                str(action.get("owner") or "-"),
                str(action.get("due_date") or "-"),
                str(action.get("reason") or "-"),
            ]
        )

    markdown = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    markdown.extend("| " + " | ".join(row) + " |" for row in rows)
    st.markdown("\n".join(markdown))


def _priority_label(priority: str | None) -> str:
    key = str(priority or "").strip().lower()
    if key == "high":
        return t("high_priority")
    if key == "medium":
        return t("medium_priority")
    if key == "low":
        return t("low_priority")
    return str(priority or "-")


def _action_status_label(status: str | None) -> str:
    key = str(status or "").strip().lower()
    labels = {
        "open": t("open_actions"),
        "in_progress": t("in_progress"),
        "completed": t("completed"),
        "cancelled": t("cancelled"),
    }
    return labels.get(key, str(status or "-").replace("_", " ").title())


def _render_tracked_actions(actions: list[dict[str, Any]], allow_complete: bool = False) -> None:
    if not actions:
        render_empty_state(t("no_tracked_actions"))
        return

    for action in actions:
        col1, col2, col3, col4, col5, col6 = st.columns([1.2, 1, 2.2, 1.2, 1, 1])
        with col1:
            st.markdown(f"**{action.get('customer_name') or action.get('customer_id')}**")
            st.caption(action.get("customer_id") or "")
        with col2:
            st.markdown(status_badge(action.get("priority"), _priority_label(action.get("priority"))), unsafe_allow_html=True)
        with col3:
            st.write(action.get("action_label") or "-")
            st.caption(action.get("reason") or "")
        with col4:
            st.write(action.get("owner") or "-")
        with col5:
            st.write(action.get("due_date") or "-")
            st.markdown(status_badge(action.get("status"), _action_status_label(action.get("status"))), unsafe_allow_html=True)
        with col6:
            st.write(action.get("evidence_count", 0))
            if allow_complete and action.get("status") in {"open", "in_progress"}:
                if st.button(t("complete_action"), key=f"complete-{action.get('action_id')}"):
                    result = complete_action(action.get("action_id"))
                    if result.ok:
                        render_success(t("action_completed"))
                        st.rerun()
                    else:
                        render_error(result.error or t("error"))
        st.divider()


def _render_priority_customer_cards(priority_rows: list[dict]) -> None:
    if not priority_rows:
        render_empty_state(t("no_priority_customers"))
        return

    for customer in priority_rows[:5]:
        score = _as_int(customer.get("risk_score"))
        level = customer.get("risk_level")
        name = _customer_name(customer)
        customer_id = _customer_external_id(customer)
        reasons = format_list_items(customer.get("top_reasons") or [], t("no_items"))
        actions = format_list_items(customer.get("recommended_actions") or [], t("no_items"))
        next_action = customer.get("next_best_action") or "-"
        owner = customer.get("owner") or "-"
        due_date = customer.get("due_date") or "-"
        st.markdown(
            f"""
            <div class="riskops-customer-card">
                <div class="riskops-customer-header">
                    <div>
                        <div class="riskops-customer-name">{html.escape(name)}</div>
                        <div class="riskops-customer-meta">{html.escape(customer_id)}</div>
                    </div>
                    <div>{risk_badge(level, _risk_label(level))}</div>
                </div>
                <div class="riskops-score-label">
                    <span>{html.escape(t("risk_score"))}</span>
                    <span>{score}/100</span>
                </div>
                <div class="riskops-score-track">
                    <div class="riskops-score-fill" style="width:{max(0, min(100, score))}%;background:{risk_color(level)};"></div>
                </div>
                <div style="height:0.85rem;"></div>
                <strong>{html.escape(t("top_reasons"))}</strong>
                {reasons}
                <strong>{html.escape(t("recommended_actions"))}</strong>
                {actions}
                <div style="height:0.5rem;"></div>
                <strong>{html.escape(t("recommended_ownership"))}</strong>
                <p>{html.escape(t("next_best_action"))}: {html.escape(str(next_action))}</p>
                <p>{html.escape(t("owner"))}: {html.escape(str(owner))} | {html.escape(t("due_date"))}: {html.escape(str(due_date))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _find_customer(customers: list[dict], customer_id: str) -> dict:
    normalized = customer_id.strip().lower()
    for customer in customers:
        if str(customer.get("customer_external_id", "")).lower() == normalized:
            return customer
    return {}


def _render_history(history: list[dict]) -> None:
    if not history:
        render_empty_state(t("no_prediction_history"))
        return
    rows = [
        {
            t("date"): item.get("created_at"),
            t("score"): item.get("risk_score"),
            t("level"): _risk_label(item.get("risk_level")),
            t("top_reasons"): ", ".join((item.get("reasons") or [])[:2]),
        }
        for item in history
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _friendly_rag_error(error: str | None) -> str:
    text = str(error or "")
    lowered = text.lower()
    if "openai" in lowered or "api key" in lowered or "embedding" in lowered or "generation" in lowered:
        return t("openai_rag_message")
    return text or t("rag_failed", error="")


def _document_status_color(status: str | None) -> str:
    key = str(status or "").lower()
    if key == "processed":
        return "#16A34A"
    if key in {"uploaded", "pending"}:
        return "#F59E0B"
    if "failed" in key or "error" in key:
        return "#DC2626"
    return "#2563EB"


def _render_footer() -> None:
    st.divider()
    st.caption(t("footer"))


def render_executive_overview() -> None:
    section_header(
        t("page.executive_overview"),
        t("executive_subtitle"),
    )

    if st.button(t("refresh_overview"), use_container_width=False):
        st.rerun()

    with st.spinner(t("loading_executive")):
        customers_result = get_customers()
        priority = get_priority_customers()
        weekly = get_weekly_report()
        health = get_health()
        ready = get_ready()
        llm_summary = get_llm_summary()
        action_plan = get_action_plan(limit=5, language=current_language())

    customers = customers_result.data if customers_result.ok and customers_result.data else []
    priority_rows = priority.data if priority.ok and priority.data else []
    report = weekly.data if weekly.ok and weekly.data else {}
    actions = _recommended_actions(priority_rows, report)
    ready_label = t("ready") if ready.ok else t("not_ready")

    if not customers_result.ok:
        render_error(t("backend_unavailable"))
    elif not customers:
        render_warning(t("no_customers"))

    _render_insight(
        t("executive_summary"),
        _business_summary(customers, priority_rows, report),
        "#2563EB",
    )

    cols = st.columns(6)
    with cols[0]:
        metric_card(t("total_customers"), report.get("total_customers", len(customers)), t("customer_base"), "#2563EB")
    with cols[1]:
        metric_card(t("high_risk_customers"), report.get("high_risk_customers", "-"), t("immediate_attention"), "#DC2626")
    with cols[2]:
        metric_card(t("medium_risk_customers"), report.get("medium_risk_customers", "-"), t("watch_this_week"), "#F59E0B")
    with cols[3]:
        metric_card(t("low_risk_customers"), report.get("low_risk_customers", "-"), t("stable_accounts"), "#16A34A")
    with cols[4]:
        metric_card(t("recommended_actions"), len(actions), t("prioritized_next_steps"), "#2563EB")
    with cols[5]:
        metric_card(t("system_status"), ready_label, t("secure_workspace"), risk_color("low" if ready.ok else "high"))

    section_header(t("top_priority_customers"), t("top_priority_subtitle"))
    if priority_rows:
        _render_priority_customer_cards(priority_rows)
    elif not priority.ok:
        render_warning(t("priority_unavailable", error=priority.error))
    else:
        render_empty_state(t("no_priority_customers"))

    section_header(t("action_plan"), t("action_plan_subtitle"))
    if action_plan.ok:
        _render_action_plan_table((action_plan.data or {}).get("actions") or [])
    else:
        render_warning(t("action_plan_unavailable", error=action_plan.error))

    col1, col2 = st.columns([1, 1])
    with col1:
        section_header(t("weekly_risk_summary"), t("weekly_risk_subtitle"))
        if report.get("executive_summary"):
            _render_insight(t("business_impact"), report["executive_summary"], "#F59E0B")
        elif weekly.ok:
            render_empty_state(t("weekly_report_empty"))
        else:
            render_warning(t("weekly_report_unavailable", error=weekly.error))

        _render_insight(
            t("main_risk_drivers"),
            "; ".join(_main_risk_drivers(priority_rows)),
            "#DC2626" if priority_rows else "#F59E0B",
        )

    with col2:
        section_header(t("todays_action_plan"), t("action_plan_subtitle"))
        _render_action_checklist(actions)

    if not ready.ok:
        render_warning(t("model_not_trained") if ready.status_code == 503 else ready.error or t("system_not_ready"))

    with st.expander(t("technical_details")):
        safe_json_preview(
            {
                "customers_status": customers_result.status_code,
                "health_status": health.status_code,
                "weekly_report": report,
                "action_plan": action_plan.data if action_plan.ok else action_plan.error,
                "readiness_status": ready.status_code,
                "llm_summary": llm_summary.data if llm_summary.ok else llm_summary.error,
            }
        )


def render_client_risk() -> None:
    section_header(
        t("page.client_risk"),
        t("client_risk_subtitle"),
    )

    if st.button(t("refresh_client_data")):
        st.rerun()

    customer_file = st.file_uploader(t("import_customer_csv"), type=["csv"], accept_multiple_files=False)
    if customer_file and st.button(t("import_customers"), type="primary"):
        with st.spinner(t("importing_customer_csv")):
            files = {
                "file": (
                    customer_file.name,
                    customer_file.getvalue(),
                    customer_file.type or "text/csv",
                )
            }
            result = safe_post("/customers/import", files=files, timeout=30)
        if result.ok:
            render_success(t("customers_imported", count=result.data.get("imported_count", 0)))
        else:
            render_error(t("customer_import_failed", error=result.error))

    with st.spinner(t("loading_customer_records")):
        customers = _customers()

    if not customers:
        render_empty_state(t("no_customers"))
        return

    section_header(t("customer_selection"), t("customer_selection_subtitle"))
    options = _customer_options(customers)
    selected_label = st.selectbox(t("select_customer"), list(options.keys()))
    default_customer_id = options[selected_label]
    manual_customer_id = st.text_input(t("enter_customer_id"), value=default_customer_id)
    selected_customer_id = manual_customer_id.strip() or default_customer_id
    selected_customer = _find_customer(customers, selected_customer_id)

    if selected_customer:
        col_a, col_b, col_c = st.columns(3)
        col_a.metric(t("customer"), selected_customer_id)
        col_b.metric(t("name"), _customer_name(selected_customer))
        col_c.metric(t("contract"), selected_customer.get("contract_type") or "-")

    if st.button(t("analyze_customer"), use_container_width=True, type="primary"):
        with st.spinner(t("analyzing_customer")):
            result = analyze_customer_risk(selected_customer_id, current_language())

        if result.ok:
            analysis = result.data
            document_risk_result = get_document_risk(selected_customer_id, current_language())
            client_360_result = get_client_360(selected_customer_id, current_language())
            document_risk = document_risk_result.data if document_risk_result.ok else {
                "document_risk_score": analysis.get("document_risk_score", 0),
                "document_risk_level": analysis.get("document_risk_level", "low"),
                "document_risk_signals": analysis.get("document_risk_signals") or [],
                "document_evidence": analysis.get("document_evidence") or [],
                "linked_documents": [],
            }
            section_header(t("customer_risk_profile"), t("customer_risk_profile_subtitle"))
            card_cols = st.columns([1.1, 1, 1])
            with card_cols[0]:
                render_risk_score(
                    analysis.get("risk_score"),
                    analysis.get("risk_level"),
                    t("risk_score"),
                    _risk_label(analysis.get("risk_level")),
                )
            with card_cols[1]:
                st.markdown(
                    f"""
                    <div class="riskops-soft-box">
                        <div class="riskops-card-title">{html.escape(t("customer"))}</div>
                        <div class="riskops-card-value">{html.escape(str(analysis.get("customer_id") or selected_customer_id))}</div>
                        <div class="riskops-card-subtitle">{html.escape(_customer_name(selected_customer) if selected_customer else t("customer_record"))}</div>
                        <div style="height:0.75rem;"></div>
                        <div>{risk_badge(analysis.get("risk_level"), _risk_label(analysis.get("risk_level")))}</div>
                        <p><strong>{html.escape(t("churn_probability"))}:</strong> {_as_percent(analysis.get("churn_probability"))}</p>
                        <p><strong>{html.escape(t("confidence"))}:</strong> {_format_confidence(analysis.get("confidence"))}</p>
                        <p><strong>{html.escape(t("prediction_id"))}:</strong> {html.escape(str(analysis.get("prediction_id", "-")))}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with card_cols[2]:
                st.markdown(
                    f"""
                    <div class="riskops-soft-box">
                        <div class="riskops-card-title">{html.escape(t("recommended_ownership"))}</div>
                        <div class="riskops-card-value" style="font-size:1.35rem;">{html.escape(str(analysis.get("owner") or "-"))}</div>
                        <div class="riskops-card-subtitle">{html.escape(t("owner"))}: {html.escape(str(analysis.get("owner") or "-"))}</div>
                        <div class="riskops-card-subtitle">{html.escape(t("due_date"))}: {html.escape(str(analysis.get("due_date") or "-"))}</div>
                        <div style="height:0.75rem;"></div>
                        <strong>{html.escape(t("next_best_action"))}</strong>
                        <p>{html.escape(str(analysis.get("next_best_action") or "-"))}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            _render_insight(
                t("business_impact"),
                str(analysis.get("business_impact") or "-"),
                "#F59E0B",
            )

            section_header(t("why_this_score"), t("score_breakdown"))
            _render_score_breakdown(analysis)

            section_header(t("document_risk"), t("documents_linked_to_customer"))
            if document_risk_result.ok:
                _render_document_risk(document_risk)
                _render_document_evidence(document_risk.get("document_evidence") or [])
            else:
                render_warning(document_risk_result.error or t("no_linked_documents"))

            section_header(t("client_360"), t("client_360_subtitle"))
            if client_360_result.ok:
                client_360 = client_360_result.data or {}
                customer_profile = client_360.get("customer") or {}
                tracked_actions = client_360.get("tracked_actions") or []
                summary_text = (
                    f"{customer_profile.get('customer_id', selected_customer_id)} - "
                    f"{customer_profile.get('name') or _customer_name(selected_customer)} | "
                    f"{t('risk_score')}: {analysis.get('risk_score')}/100 | "
                    f"{t('document_risk_score')}: {document_risk.get('document_risk_score', 0)}/100"
                )
                _render_insight(t("client_360"), summary_text, "#2563EB")
                st.markdown(f"#### {t('tracked_actions')}")
                for status_key in ["open", "in_progress", "completed"]:
                    status_actions = [
                        action for action in tracked_actions if action.get("status") == status_key
                    ]
                    st.markdown(f"##### {_action_status_label(status_key)}")
                    _render_tracked_actions(status_actions, allow_complete=False)
            else:
                render_warning(client_360_result.error or t("system_not_ready"))

            col1, col2 = st.columns([1, 1])
            with col1:
                _render_insight(t("main_risk_drivers"), t("main_risk_drivers_detail"), "#DC2626")
                st.markdown(format_list_items(analysis.get("reasons"), t("no_items")), unsafe_allow_html=True)
            with col2:
                _render_insight(t("recommended_next_step"), t("recommended_next_step_detail"), "#2563EB")
                _render_action_checklist(analysis.get("recommended_actions") or [])

            with st.expander(t("technical_details")):
                safe_json_preview(analysis)

            with st.spinner(t("loading_risk_history")):
                history = get_risk_history(selected_customer_id)
            section_header(t("customer_risk_history"), t("customer_risk_history_subtitle"))
            if history.ok:
                _render_history(history.data or [])
            else:
                render_warning(t("prediction_history_unavailable", error=history.error))
        else:
            if result.status_code == 503:
                render_error(t("model_not_trained"))
            elif result.status_code == 404:
                render_error(t("requested_customer_not_found"))
            else:
                render_error(t("riskops_analysis_failed", error=result.error))

    with st.expander(t("customer_records")):
        _risk_table(customers)


def render_action_board() -> None:
    section_header(t("page.action_board"), t("action_board_subtitle"))

    sync_cols = st.columns([1, 3])
    with sync_cols[0]:
        if st.button(t("sync_recommended_actions"), use_container_width=True, type="primary"):
            with st.spinner(t("syncing_actions")):
                result = sync_recommended_actions(limit=10, language=current_language())
            if result.ok:
                render_success(t("actions_synced", count=len(result.data or [])))
                st.rerun()
            else:
                render_error(t("action_sync_failed", error=result.error))

    board = get_action_board(language=current_language(), limit=200)
    all_actions_result = get_actions(limit=200)
    all_actions = all_actions_result.data if all_actions_result.ok and all_actions_result.data else []
    summary = (board.data or {}).get("summary", {}) if board.ok else {}

    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        metric_card(t("open_actions"), summary.get("open_actions", 0), t("tracked_actions"), "#2563EB")
    with kpi_cols[1]:
        metric_card(t("in_progress"), summary.get("in_progress", 0), t("tracked_actions"), "#F59E0B")
    with kpi_cols[2]:
        metric_card(t("completed"), summary.get("completed", 0), t("tracked_actions"), "#16A34A")
    with kpi_cols[3]:
        metric_card(t("overdue"), summary.get("overdue", 0), t("due_date"), "#DC2626")
    with kpi_cols[4]:
        metric_card(t("high_priority"), summary.get("high_priority", 0), t("priority"), "#DC2626")

    owners = sorted({str(action.get("owner")) for action in all_actions if action.get("owner")})
    filter_cols = st.columns(3)
    status_options = ["", "open", "in_progress", "completed", "cancelled"]
    priority_options = ["", "high", "medium", "low"]
    with filter_cols[0]:
        selected_status = st.selectbox(
            t("filter_by_status"),
            status_options,
            format_func=lambda value: t("all") if value == "" else _action_status_label(value),
        )
    with filter_cols[1]:
        selected_owner = st.selectbox(
            t("filter_by_owner"),
            [""] + owners,
            format_func=lambda value: t("all") if value == "" else value,
        )
    with filter_cols[2]:
        selected_priority = st.selectbox(
            t("filter_by_priority"),
            priority_options,
            format_func=lambda value: t("all") if value == "" else _priority_label(value),
        )

    filtered = get_actions(
        status=selected_status or None,
        owner=selected_owner or None,
        priority=selected_priority or None,
        limit=200,
    )

    section_header(t("tracked_actions"), t("action_board_subtitle"))
    if filtered.ok:
        _render_tracked_actions(filtered.data or [], allow_complete=True)
    else:
        render_error(filtered.error or t("error"))

    with st.expander(t("technical_details")):
        safe_json_preview(
            {
                "board": board.data if board.ok else board.error,
                "filters": {
                    "status": selected_status,
                    "owner": selected_owner,
                    "priority": selected_priority,
                },
            }
        )


def render_documents_rag() -> None:
    section_header(
        t("page.documents_rag"),
        t("documents_subtitle"),
    )

    if st.button(t("refresh_documents")):
        st.rerun()

    _render_insight(
        t("document_guidance_title"),
        t("document_guidance_body"),
        "#2563EB",
    )

    uploaded_files = st.file_uploader(
        t("upload_document"),
        type=["pdf", "csv"],
        accept_multiple_files=True,
    )

    if uploaded_files and st.button(t("upload_selected_files"), type="primary"):
        for uploaded_file in uploaded_files:
            with st.spinner(t("uploading_file", filename=uploaded_file.name)):
                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type or "application/octet-stream",
                    )
                }
                result = safe_post("/documents/upload", files=files, timeout=30)
            if result.ok:
                render_success(
                    t(
                        "uploaded_document",
                        filename=result.data.get("filename"),
                        document_id=result.data.get("id"),
                    )
                )
            else:
                render_error(t("upload_failed", filename=uploaded_file.name, error=result.error))

    with st.spinner(t("loading_documents")):
        documents_result = get_documents()
    if not documents_result.ok:
        render_warning(t("document_list_unavailable", error=documents_result.error))
        return

    documents = documents_result.data or []
    if not documents:
        render_empty_state(t("no_documents"))
        return

    section_header(t("document_library"), t("document_library_subtitle"))
    status_counts = {}
    for document in documents:
        status = str(document.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    status_cols = st.columns(3)
    status_cols[0].metric(t("documents"), len(documents))
    status_cols[1].metric(t("processed"), status_counts.get("processed", 0))
    status_cols[2].metric(t("needs_processing"), len(documents) - status_counts.get("processed", 0))

    rows = [
        {
            "ID": document.get("id"),
            t("filename"): document.get("filename"),
            t("type"): document.get("document_type"),
            t("status"): _status_label(document.get("status")),
            t("processed_at"): document.get("processed_at"),
        }
        for document in documents
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    options = {
        f"{document.get('id')} - {document.get('filename')} ({document.get('status')})": document.get("id")
        for document in documents
    }
    selected_label = st.selectbox(t("documents"), list(options.keys()))
    selected_document_id = options[selected_label]
    selected_document = next((doc for doc in documents if doc.get("id") == selected_document_id), {})
    selected_status = selected_document.get("status")

    st.markdown(
        f"""
        <div class="riskops-soft-box">
            <div class="riskops-card-title">{html.escape(t("selected_document"))}</div>
            <div class="riskops-card-value">{html.escape(str(selected_document.get("filename") or selected_label))}</div>
            <div class="riskops-card-subtitle">{html.escape(t("status"))}: {status_badge(selected_status, _status_label(selected_status))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button(t("process_selected_document"), use_container_width=True):
            with st.spinner(t("processing_document")):
                result = safe_post(f"/documents/{selected_document_id}/process", timeout=120)
            if result.ok:
                render_success(
                    t(
                        "document_processed",
                        document_id=result.data.get("document_id"),
                        chunks=result.data.get("chunks_created"),
                    )
                )
            else:
                render_error(t("processing_failed", error=_friendly_rag_error(result.error)))

    with col2:
        if str(selected_status).lower() != "processed":
            render_warning(t("document_not_processed"))
        else:
            render_success(t("document_ready"))

    section_header(t("ask_question"), t("ask_question_subtitle"))
    with st.form("rag-question-form"):
        question = st.text_input(
            t("question"),
            value=t("rag_default_question"),
        )
        ask_submitted = st.form_submit_button(t("ask_copilot"))

    if ask_submitted:
        result = ask_rag(question, selected_document_id, current_language())
        if result.ok:
            answer = result.data.get("answer") or t("no_answer_returned")
            st.markdown(f"#### {t('rag_answer')}")
            _render_insight(t("answer"), answer, "#2563EB")
            _render_structured_response(result.data)
            _render_sources(result.data.get("sources") or [])

            with st.expander(t("technical_details")):
                safe_json_preview(result.data)
        else:
            render_error(t("rag_failed", error=_friendly_rag_error(result.error)))


def render_ai_assistant() -> None:
    section_header(
        t("ai_assistant_title"),
        t("ai_assistant_subtitle"),
    )

    if "agent_question" not in st.session_state:
        st.session_state.agent_question = t("default_agent_question")

    quick_questions = [
        t("quick_q_priority"),
        t("quick_q_weekly"),
        t("quick_q_customer"),
        t("quick_q_actions"),
    ]

    st.markdown(f"#### {t('quick_questions')}")
    quick_cols = st.columns(4)
    for index, question in enumerate(quick_questions):
        if quick_cols[index].button(question, use_container_width=True):
            st.session_state.agent_question = question
            st.rerun()

    if st.button(t("clear_question")):
        st.session_state.agent_question = ""
        st.rerun()

    with st.form("riskops-agent-form"):
        question = st.text_input(t("question"), key="agent_question")
        submitted = st.form_submit_button(t("ask_agent"), type="primary")

    if submitted:
        if not question.strip():
            render_warning(t("enter_question"))
            return

        with st.spinner(t("running_agent")):
            result = analyze_agent(question, current_language())

        if result.ok:
            data = result.data or {}
            st.markdown(f"#### {t('answer')}")
            st.markdown(
                f"""
                <div class="riskops-insight-box" style="border-left-color:#2563EB;">
                    <div class="riskops-insight-title">{html.escape(t("agent_response"))}</div>
                    <div class="riskops-insight-body">{html.escape(str(data.get("answer") or t("no_answer_returned")))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            selected_tool = data.get("selected_tool") or "agent_tool"
            st.markdown(status_badge(selected_tool, str(selected_tool).replace("_", " ").title()), unsafe_allow_html=True)
            _render_structured_response(data)
            sources = data.get("sources") or []
            if sources:
                _render_sources(sources)

            summary_data = data.get("data") or {}
            if isinstance(summary_data, dict) and summary_data:
                st.markdown(f"#### {t('data_summary')}")
                summary_items = []
                for key, value in list(summary_data.items())[:5]:
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        summary_items.append(f"{key}: {value}")
                    elif isinstance(value, list):
                        summary_items.append(f"{key}: {t('items_count', count=len(value))}")
                    else:
                        summary_items.append(f"{key}: {t('available_value')}")
                st.markdown(format_list_items(summary_items, t("no_items")), unsafe_allow_html=True)

            with st.expander(t("technical_details")):
                safe_json_preview(data)
        else:
            render_error(t("agent_failed", error=result.error))


def render_data_pipeline() -> None:
    section_header(
        t("page.data_pipeline"),
        t("data_pipeline_subtitle"),
    )

    if st.button(t("refresh_pipeline_status")):
        st.rerun()

    with st.spinner(t("checking_pipeline")):
        health = get_health()
        ready = get_ready()
        weekly = get_weekly_report()

    cols = st.columns(4)
    with cols[0]:
        metric_card(t("backend"), t("ready") if ready.ok else t("not_ready"), ready.error or t("fastapi_readiness"), risk_color("low" if ready.ok else "high"))
    with cols[1]:
        metric_card("Airflow DAG", "riskops_daily_pipeline", t("workflow_status"), "#2563EB")
    with cols[2]:
        metric_card("dbt", t("sql_transforms"), "staging -> intermediate -> mart", "#2563EB")
    with cols[3]:
        metric_card(t("api_health"), t("healthy") if health.ok else t("error"), t("backend_api_check"), risk_color("low" if health.ok else "high"))

    st.link_button(t("open_workflow_orchestration"), "http://localhost:8080", use_container_width=False)

    col1, col2 = st.columns([1, 1])
    with col1:
        _render_insight(
            t("airflow_role"),
            t("airflow_role_body"),
            "#2563EB",
        )
    with col2:
        _render_insight(
            t("dbt_role"),
            t("dbt_role_body"),
            "#2563EB",
        )

    section_header(t("pipeline_tasks"), t("pipeline_tasks_subtitle"))
    task_cols = st.columns(2)
    for index, task in enumerate(PIPELINE_TASKS):
        with task_cols[index % 2]:
            st.markdown(status_badge("ready", t("ready")) + f" {html.escape(_pipeline_task_label(task))}", unsafe_allow_html=True)

    section_header(t("data_flow"), t("data_flow_subtitle"))
    st.markdown(
        f"""
        <div class="riskops-soft-box">
        {t("data_flow_html")}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if weekly.ok and weekly.data:
        section_header(t("latest_weekly_output"), t("latest_weekly_output_subtitle"))
        report = weekly.data
        report_cols = st.columns(3)
        report_cols[0].metric(t("total_customers_metric"), report.get("total_customers"))
        report_cols[1].metric(t("high_risk_metric"), report.get("high_risk_customers"))
        report_cols[2].metric(t("medium_risk_metric"), report.get("medium_risk_customers"))
        _render_insight(t("weekly_report_summary"), report.get("executive_summary") or t("weekly_report_no_summary"), "#F59E0B")
    else:
        render_warning(t("weekly_report_unavailable", error=weekly.error))

    with st.expander(t("technical_details")):
        safe_json_preview(
            {
                "health": health.data if health.ok else health.error,
                "ready": ready.data if ready.ok else ready.error,
                "weekly_report": weekly.data if weekly.ok else weekly.error,
                "dag_name": "riskops_daily_pipeline",
                "tasks": PIPELINE_TASKS,
            }
        )


def render_monitoring() -> None:
    section_header(
        t("page.monitoring"),
        t("monitoring_subtitle"),
    )

    if st.button(t("refresh_monitoring")):
        st.rerun()

    with st.spinner(t("loading_monitoring")):
        health = get_health()
        ready = get_ready()
        llm_summary = get_llm_summary()
        ml_report = get_ml_report_status()

    cols = st.columns(4)
    with cols[0]:
        metric_card(t("api_health"), t("healthy") if health.ok else t("error"), health.error or t("api_and_database"), risk_color("low" if health.ok else "high"))
    with cols[1]:
        metric_card(t("readiness"), t("ready") if ready.ok else t("not_ready"), ready.error or t("tables_model_folders"), risk_color("low" if ready.ok else "high"))
    with cols[2]:
        total_traces = llm_summary.data.get("total_traces") if llm_summary.ok and llm_summary.data else "-"
        metric_card(t("llm_traces"), total_traces, t("rag_agent_calls"), "#2563EB")
    with cols[3]:
        report_exists = ml_report.data.get("report_exists") if ml_report.ok and isinstance(ml_report.data, dict) else False
        metric_card(t("ml_report"), t("available") if report_exists else t("missing"), t("data_quality_html"), risk_color("low" if report_exists else "medium"))

    status_col1, status_col2 = st.columns([1, 1])
    with status_col1:
        st.markdown(f"#### {t('service_status')}")
        st.markdown(status_badge("healthy" if health.ok else "error", t("healthy") if health.ok else t("error")) + f" {t('api_health')}", unsafe_allow_html=True)
        st.markdown(status_badge("ready" if ready.ok else "warning", t("ready") if ready.ok else t("warning")) + f" {t('readiness')}", unsafe_allow_html=True)
    with status_col2:
        st.markdown(f"#### {t('report_status')}")
        if ml_report.ok and isinstance(ml_report.data, dict) and ml_report.data.get("report_exists"):
            st.markdown(status_badge("healthy", t("healthy")) + f" {t('ml_report_available')}", unsafe_allow_html=True)
        else:
            st.markdown(status_badge("warning", t("warning")) + f" {t('no_ml_report')}", unsafe_allow_html=True)
            render_empty_state(t("no_ml_report"))

    if st.button(t("generate_ml_report"), type="primary"):
        with st.spinner(t("generating_ml_report")):
            result = safe_post("/monitoring/ml/generate-report", timeout=120)
        if result.ok:
            render_success(result.data.get("summary", t("ml_report_generated")))
        else:
            render_error(t("ml_report_generation_failed", error=result.error))

    if ml_report.ok and isinstance(ml_report.data, dict) and ml_report.data.get("report_exists"):
        st.link_button(t("open_html_report"), "http://localhost:8000/monitoring/ml/report?format=html")

    traces = get_llm_traces(limit=10)
    if traces.ok and traces.data:
        section_header(t("recent_llm_calls"), t("recent_llm_calls_subtitle"))
        trace_rows = [
            {
                "Timestamp": trace.get("timestamp"),
                "Operation": trace.get("operation"),
                "Tool": trace.get("selected_tool"),
                "Status": trace.get("status"),
                "Latency ms": trace.get("latency_ms"),
                "Sources": trace.get("number_of_sources"),
            }
            for trace in reversed(traces.data)
        ]
        st.dataframe(pd.DataFrame(trace_rows), use_container_width=True, hide_index=True)
    elif traces.ok:
        render_empty_state(t("no_llm_trace"))
    else:
        render_warning(t("llm_traces_unavailable", error=traces.error))

    with st.expander(t("technical_details")):
        safe_json_preview(
            {
                "health": health.data if health.ok else health.error,
                "ready": ready.data if ready.ok else ready.error,
                "llm_summary": llm_summary.data if llm_summary.ok else llm_summary.error,
                "llm_traces": traces.data if traces.ok else traces.error,
                "ml_report": ml_report.data if ml_report.ok else ml_report.error,
            }
        )


def render_about_project() -> None:
    section_header(
        t("page.about_project"),
        t("about_subtitle"),
    )

    cols = st.columns(3)
    with cols[0]:
        metric_card(t("backend"), "FastAPI", t("product_apis"), "#2563EB")
    with cols[1]:
        metric_card(t("data"), "PostgreSQL + pgvector", t("business_vector_storage"), "#2563EB")
    with cols[2]:
        metric_card("AI", "RAG + ML + Agent", t("documents_prediction_routing"), "#2563EB")

    content = [
        (
            t("business_problem"),
            t("business_problem_body"),
            "#DC2626",
        ),
        (
            t("solution"),
            t("solution_body"),
            "#2563EB",
        ),
        (
            t("architecture_summary"),
            t("architecture_summary_body"),
            "#2563EB",
        ),
        (
            t("main_features"),
            t("main_features_body"),
            "#16A34A",
        ),
        (
            t("technology_stack"),
            t("technology_stack_body"),
            "#2563EB",
        ),
        (
            t("governance_monitoring"),
            t("governance_monitoring_body"),
            "#16A34A",
        ),
        (
            t("operational_scope"),
            t("operational_scope_body"),
            "#F59E0B",
        ),
        (
            t("next_improvements"),
            t("next_improvements_body"),
            "#2563EB",
        ),
    ]

    for index in range(0, len(content), 2):
        col1, col2 = st.columns(2)
        for column, item in zip([col1, col2], content[index : index + 2]):
            with column:
                _render_insight(item[0], item[1], item[2])

    section_header(t("operational_focus"), t("operational_focus_subtitle"))
    _render_action_checklist(
        [
            t("page.executive_overview"),
            t("page.client_risk"),
            t("page.ai_assistant"),
            t("page.documents_rag"),
            t("page.data_pipeline"),
            t("page.monitoring"),
        ]
    )


def main() -> None:
    active_page = render_sidebar()
    render_product_header()

    if active_page == "executive_overview":
        render_executive_overview()
    elif active_page == "client_risk":
        render_client_risk()
    elif active_page == "action_board":
        render_action_board()
    elif active_page == "documents_rag":
        render_documents_rag()
    elif active_page == "ai_assistant":
        render_ai_assistant()
    elif active_page == "data_pipeline":
        render_data_pipeline()
    elif active_page == "monitoring":
        render_monitoring()
    elif active_page == "about_project":
        render_about_project()

    _render_footer()


if __name__ == "__main__":
    main()
