import html
import json
from typing import Any

import streamlit as st


RISK_COLORS = {
    "high": "#DC2626",
    "medium": "#F59E0B",
    "low": "#16A34A",
    "healthy": "#16A34A",
    "warning": "#F59E0B",
    "error": "#DC2626",
}


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --riskops-primary: #2563EB;
            --riskops-text: #111827;
            --riskops-muted: #6B7280;
            --riskops-bg: #F3F4F6;
            --riskops-card: #FFFFFF;
            --riskops-border: #E5E7EB;
        }

        .main .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2rem;
            max-width: 1280px;
        }

        h1, h2, h3 {
            color: var(--riskops-text);
            letter-spacing: 0;
        }

        div[data-testid="stSidebar"] {
            background: #FFFFFF;
            border-right: 1px solid var(--riskops-border);
        }

        div[data-testid="stMetric"] {
            background: var(--riskops-card);
            border: 1px solid var(--riskops-border);
            border-radius: 8px;
            padding: 1rem;
        }

        .riskops-product-header {
            background: #FFFFFF;
            border: 1px solid var(--riskops-border);
            border-radius: 8px;
            padding: 1.25rem 1.4rem;
            margin-bottom: 1rem;
        }

        .riskops-product-header h1 {
            margin: 0;
            font-size: 2rem;
            line-height: 1.15;
        }

        .riskops-product-header p {
            margin: 0.4rem 0 0 0;
            color: var(--riskops-muted);
            font-size: 1rem;
        }

        .riskops-card {
            background: #FFFFFF;
            border: 1px solid var(--riskops-border);
            border-radius: 8px;
            padding: 1rem;
            min-height: 120px;
        }

        .riskops-card-title {
            color: #6B7280;
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }

        .riskops-card-value {
            color: var(--riskops-text);
            font-size: 1.8rem;
            font-weight: 800;
            line-height: 1.1;
        }

        .riskops-card-subtitle {
            color: #6B7280;
            margin-top: 0.45rem;
            font-size: 0.9rem;
        }

        .riskops-section {
            margin: 1.2rem 0 0.75rem 0;
        }

        .riskops-section h2 {
            margin: 0;
            font-size: 1.45rem;
        }

        .riskops-section p {
            margin: 0.25rem 0 0 0;
            color: #6B7280;
        }

        .riskops-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            border-radius: 999px;
            color: #FFFFFF;
            font-size: 0.78rem;
            font-weight: 800;
            line-height: 1;
            padding: 0.38rem 0.62rem;
            text-transform: uppercase;
            white-space: nowrap;
        }

        .riskops-soft-box {
            background: #FFFFFF;
            border: 1px solid var(--riskops-border);
            border-radius: 8px;
            padding: 1rem;
        }

        .riskops-insight-box {
            background: #FFFFFF;
            border: 1px solid var(--riskops-border);
            border-left: 4px solid var(--riskops-primary);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.75rem;
        }

        .riskops-insight-title {
            color: var(--riskops-text);
            font-size: 0.98rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
        }

        .riskops-insight-body {
            color: #374151;
            font-size: 0.95rem;
            line-height: 1.45;
        }

        .riskops-customer-card {
            background: #FFFFFF;
            border: 1px solid var(--riskops-border);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.8rem;
        }

        .riskops-customer-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.75rem;
        }

        .riskops-customer-name {
            color: var(--riskops-text);
            font-weight: 800;
            font-size: 1.05rem;
        }

        .riskops-customer-meta {
            color: #6B7280;
            font-size: 0.85rem;
            margin-top: 0.12rem;
        }

        .riskops-checklist {
            list-style: none;
            margin: 0;
            padding: 0;
        }

        .riskops-checklist li {
            background: #FFFFFF;
            border: 1px solid var(--riskops-border);
            border-radius: 8px;
            margin-bottom: 0.55rem;
            padding: 0.75rem 0.85rem;
        }

        .riskops-check {
            color: #2563EB;
            font-weight: 900;
            margin-right: 0.45rem;
        }

        .riskops-empty {
            background: #F9FAFB;
            border: 1px dashed #D1D5DB;
            border-radius: 8px;
            color: #6B7280;
            padding: 1rem;
        }

        .riskops-score-track {
            width: 100%;
            height: 0.8rem;
            background: #E5E7EB;
            border-radius: 999px;
            overflow: hidden;
            margin-top: 0.6rem;
        }

        .riskops-score-fill {
            height: 100%;
            border-radius: 999px;
        }

        .riskops-score-label {
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #374151;
            font-size: 0.9rem;
            font-weight: 700;
        }

        .riskops-list {
            margin: 0;
            padding-left: 1.2rem;
        }

        .riskops-list li {
            margin-bottom: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def risk_color(level: str | None) -> str:
    key = str(level or "").strip().lower()
    return RISK_COLORS.get(key, "#2563EB")


def risk_badge(level: str | None, label: str | None = None) -> str:
    label = html.escape(str(label or level or "unknown").title())
    color = risk_color(level)
    return f'<span class="riskops-badge" style="background:{color};">{label}</span>'


def status_badge(status: str | None, label: str | None = None) -> str:
    key = str(status or "unknown").strip().lower()
    if key in {"ok", "ready", "healthy", "processed", "success", "online"}:
        color = "#16A34A"
    elif key in {"warning", "degraded", "uploaded", "pending"}:
        color = "#F59E0B"
    elif key in {"error", "failed", "processing_failed", "unavailable", "not_ready"}:
        color = "#DC2626"
    else:
        color = "#2563EB"
    label = html.escape(str(label or status or "unknown").replace("_", " ").title())
    return f'<span class="riskops-badge" style="background:{color};">{label}</span>'


def metric_card(title: str, value: Any, subtitle: str = "", color: str = "#2563EB") -> None:
    st.markdown(
        f"""
        <div class="riskops-card" style="border-top: 4px solid {html.escape(color)};">
            <div class="riskops-card-title">{html.escape(title)}</div>
            <div class="riskops-card-value">{html.escape(str(value))}</div>
            <div class="riskops-card-subtitle">{html.escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="riskops-section">
            <h2>{html.escape(title)}</h2>
            <p>{html.escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(message: str) -> None:
    st.markdown(
        f'<div class="riskops-empty">{html.escape(message)}</div>',
        unsafe_allow_html=True,
    )


def render_error(message: str) -> None:
    st.error(message, icon=None)


def render_success(message: str) -> None:
    st.success(message, icon=None)


def render_warning(message: str) -> None:
    st.warning(message, icon=None)


def render_risk_score(
    score: int | float | None,
    level: str | None,
    label: str = "Risk score",
    badge_label: str | None = None,
) -> None:
    numeric_score = int(score or 0)
    numeric_score = max(0, min(100, numeric_score))
    color = risk_color(level)
    st.markdown(
        f"""
        <div class="riskops-soft-box">
            <div class="riskops-score-label">
                <span>{html.escape(label)}</span>
                <span>{numeric_score}/100 {risk_badge(level, badge_label)}</span>
            </div>
            <div class="riskops-score-track">
                <div class="riskops-score-fill" style="width:{numeric_score}%;background:{color};"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_list_items(
    items: list[str] | tuple[str, ...] | None,
    empty_message: str = "No items available.",
) -> str:
    if not items:
        return f"<p>{html.escape(empty_message)}</p>"
    list_items = "".join(f"<li>{html.escape(str(item))}</li>" for item in items)
    return f'<ul class="riskops-list">{list_items}</ul>'


def safe_json_preview(data: Any) -> None:
    st.code(json.dumps(data, indent=2, ensure_ascii=True, default=str), language="json")
