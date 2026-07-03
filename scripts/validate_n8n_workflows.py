from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MAIN_WORKFLOW = ROOT / "docs" / "n8n" / "ai-riskops-github-maintainer.json"
ERROR_WORKFLOW = ROOT / "docs" / "n8n" / "ai-riskops-error-handler.json"

OPENAI_PROJECT_PREFIX = "sk" + "-proj"
GITHUB_TOKEN_PREFIX = "github" + "_pat"
BEARER_OPENAI_PREFIX = "Bearer " + "sk-"
BEARER_GITHUB_PREFIX = "Bearer " + GITHUB_TOKEN_PREFIX
RAW_CUSTOMER_PREFIX = "CUST" + "-"

SECRET_PATTERNS = [
    re.compile(re.escape(OPENAI_PROJECT_PREFIX) + r"[A-Za-z0-9_-]+"),
    re.compile(re.escape(BEARER_OPENAI_PREFIX) + r"[A-Za-z0-9_-]+"),
    re.compile(re.escape(GITHUB_TOKEN_PREFIX) + r"_[A-Za-z0-9_-]+"),
    re.compile(re.escape(BEARER_GITHUB_PREFIX) + r"_[A-Za-z0-9_-]+"),
]
CUSTOMER_ID_PATTERN = re.compile(re.escape(RAW_CUSTOMER_PREFIX))


def load_json(path: Path) -> tuple[dict[str, Any] | None, str]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except FileNotFoundError:
        return None, f"{path} does not exist"
    except json.JSONDecodeError as exc:
        return None, f"{path} is not valid JSON: {exc}"


def node_names(workflow: dict[str, Any]) -> set[str]:
    return {str(node.get("name", "")) for node in workflow.get("nodes", [])}


def find_node(workflow: dict[str, Any], name: str) -> dict[str, Any] | None:
    for node in workflow.get("nodes", []):
        if node.get("name") == name:
            return node
    return None


def contains_secret_or_customer_id(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for pattern in SECRET_PATTERNS:
        if pattern.search(raw):
            errors.append(f"{path}: forbidden secret pattern found: {pattern.pattern}")
    if CUSTOMER_ID_PATTERN.search(raw):
        errors.append(f"{path}: literal raw customer identifier prefix found")
    return errors


def require_nodes(path: Path, workflow: dict[str, Any], required: list[str]) -> list[str]:
    names = node_names(workflow)
    return [f"{path}: missing node '{name}'" for name in required if name not in names]


def validate_main() -> list[str]:
    errors: list[str] = []
    workflow, error = load_json(MAIN_WORKFLOW)
    if error:
        return [error]
    assert workflow is not None

    if workflow.get("active") is not False:
        errors.append(f"{MAIN_WORKFLOW}: workflow active must be false")

    schedule = find_node(workflow, "Schedule Trigger")
    if schedule is None:
        errors.append(f"{MAIN_WORKFLOW}: missing Schedule Trigger node")
    elif schedule.get("disabled") is not True:
        errors.append(f"{MAIN_WORKFLOW}: Schedule Trigger must be disabled")

    errors.extend(
        require_nodes(
            MAIN_WORKFLOW,
            workflow,
            [
                "RiskOps Quality Gate",
                "Is Quality Gate Passed?",
                "Search Existing Weekly Issue",
                "Weekly Issue Already Exists?",
                "Skip Duplicate Weekly Run",
                "Create an issue",
                "Create Weekly Report File",
                "Final Automation Summary",
            ],
        )
    )
    errors.extend(contains_secret_or_customer_id(MAIN_WORKFLOW))
    return errors


def validate_error_handler() -> list[str]:
    if not ERROR_WORKFLOW.exists():
        print("INFO: Error Handler workflow JSON not present; skipping optional validation.")
        return []

    errors: list[str] = []
    workflow, error = load_json(ERROR_WORKFLOW)
    if error:
        return [error]
    assert workflow is not None

    errors.extend(
        require_nodes(
            ERROR_WORKFLOW,
            workflow,
            [
                "Error Trigger",
                "Format Error Summary",
                "Create Error Incident Issue",
            ],
        )
    )
    errors.extend(contains_secret_or_customer_id(ERROR_WORKFLOW))
    return errors


def main() -> int:
    errors = validate_main()
    errors.extend(validate_error_handler())

    if errors:
        print("n8n workflow validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("n8n workflow validation passed.")
    print("- main workflow JSON valid")
    print("- workflow active is false")
    print("- Schedule Trigger is disabled")
    print("- required hardening nodes are present")
    print("- no forbidden secret or customer identifier patterns found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
