from datetime import date

from sqlalchemy.exc import SQLAlchemyError

import app.api.actions as actions_api
import app.services.action_service as action_service
from app.schemas import ActionPlanItem, ActionPlanResponse


class FakeActionDb:
    def __init__(self):
        self.actions = []
        self.rollback_called = False

    def add(self, action):
        self.actions.append(action)

    def commit(self):
        return None

    def refresh(self, _action):
        return None

    def rollback(self):
        self.rollback_called = True


def action_plan():
    return ActionPlanResponse(
        summary="One action",
        language="en",
        actions=[
            ActionPlanItem(
                action_id="act-sample-review",
                customer_id="sample-account",
                customer_name="Account Alpha",
                risk_level="high",
                priority="high",
                action_label="Review account",
                reason="Payment risk",
                owner="Finance Team",
                due_date=date.today().isoformat(),
                evidence_count=1,
                status="open",
            )
        ],
    )


def test_action_sync_is_idempotent(monkeypatch):
    db = FakeActionDb()
    monkeypatch.setattr(action_service, "generate_action_plan", lambda **_kwargs: action_plan())
    monkeypatch.setattr(
        action_service,
        "_find_open_duplicate",
        lambda db, customer_id, action_label: next(
            (
                action
                for action in db.actions
                if action.customer_id == customer_id and action.action_label == action_label
            ),
            None,
        ),
    )
    monkeypatch.setattr(action_service, "get_action_or_none", lambda _db, _id: None)

    first = action_service.sync_recommended_actions(db)
    second = action_service.sync_recommended_actions(db)

    assert len(first) == 1
    assert len(second) == 1
    assert len(db.actions) == 1
    assert first[0] is second[0]


def test_action_sync_database_failure_returns_500(client_factory, monkeypatch):
    db = FakeActionDb()
    monkeypatch.setattr(
        actions_api,
        "sync_recommended_actions",
        lambda **_kwargs: (_ for _ in ()).throw(SQLAlchemyError("failure")),
    )

    with client_factory(db) as client:
        response = client.post("/actions/sync")

    assert response.status_code == 500
    assert db.rollback_called is True
