import json
import time
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from app.core.config import settings


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def trace_llm_call(
    *,
    operation: str,
    question: str,
    document_id: int | None = None,
    selected_tool: str | None = None,
) -> Iterator[dict[str, Any]]:
    started_at = time.perf_counter()
    trace: dict[str, Any] = {
        "timestamp": utc_now_iso(),
        "operation": operation,
        "question": question,
        "document_id": document_id,
        "selected_tool": selected_tool,
        "latency_ms": None,
        "status": "success",
        "error": None,
        "number_of_sources": 0,
        "estimated_cost": None,
    }

    try:
        yield trace
    except Exception as exc:
        trace["status"] = "error"
        trace["error"] = extract_error_message(exc)
        raise
    finally:
        trace["latency_ms"] = round((time.perf_counter() - started_at) * 1000, 2)
        write_trace(trace)
        send_langfuse_trace(trace)


def write_trace(trace: dict[str, Any]) -> None:
    path = Path(settings.llm_traces_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as trace_file:
        trace_file.write(json.dumps(trace, ensure_ascii=True) + "\n")


def extract_error_message(exc: Exception) -> str:
    detail = getattr(exc, "detail", None)
    if detail:
        return str(detail)
    return str(exc) or exc.__class__.__name__


def read_traces(limit: int = 50) -> list[dict[str, Any]]:
    path = Path(settings.llm_traces_path)
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()
    traces: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        try:
            traces.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return traces


def summarize_traces() -> dict[str, Any]:
    traces = read_traces(limit=1000)
    total_traces = len(traces)
    success_count = sum(1 for trace in traces if trace.get("status") == "success")
    error_count = sum(1 for trace in traces if trace.get("status") == "error")
    latencies = [
        float(trace["latency_ms"])
        for trace in traces
        if isinstance(trace.get("latency_ms"), int | float)
    ]
    tools = Counter(
        trace.get("selected_tool") or trace.get("operation") or "unknown"
        for trace in traces
    )

    return {
        "total_traces": total_traces,
        "success_count": success_count,
        "error_count": error_count,
        "average_latency_ms": round(sum(latencies) / len(latencies), 2)
        if latencies
        else 0,
        "most_used_tools": dict(tools.most_common(5)),
        "last_trace_at": traces[-1].get("timestamp") if traces else None,
    }


def send_langfuse_trace(trace: dict[str, Any]) -> None:
    if not settings.enable_langfuse:
        return
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return

    try:
        from langfuse import Langfuse
    except Exception:
        return

    try:
        client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        client.trace(
            name=trace.get("operation", "riskops-llm-call"),
            input=trace.get("question"),
            output={
                "status": trace.get("status"),
                "selected_tool": trace.get("selected_tool"),
                "number_of_sources": trace.get("number_of_sources"),
            },
            metadata={
                "latency_ms": trace.get("latency_ms"),
                "document_id": trace.get("document_id"),
                "error": trace.get("error"),
            },
        )
        client.flush()
    except Exception:
        return
