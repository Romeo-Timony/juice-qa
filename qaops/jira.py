"""Jira side effects routed through idempotency keys + resilient transport."""

from typing import Optional

from qaops import idempotency
from qaops.config import settings
from qaops.resilience import TransientFailure, resilient_request


def _issue_url(issue_key: str, suffix: str = "") -> str:
    return f"{settings.jira_url}/rest/api/2/issue/{issue_key}{suffix}"


def comment_once(issue_key: str, body: str, scope_key: Optional[str] = None) -> Optional[str]:
    """Posts a comment at most once per (issue, scope_key or body)."""
    try:
        with idempotency.idempotent("jira.comment", issue_key, scope_key or body) as g:
            if g.duplicate:
                return g.result.get("id")
            key = idempotency.make_key("jira.comment", issue_key, scope_key or body)
            resp = resilient_request("POST", _issue_url(issue_key, "/comment"), auth=settings.jira_auth, json={"body": body}, idem_key=key)
            if not resp.ok:
                raise RuntimeError(f"Jira comment HTTP {resp.status_code}: {resp.text[:200]}")
            cid = resp.json().get("id")
            g.complete({"id": cid})
            return cid
    except (TransientFailure, RuntimeError, idempotency.DuplicateInFlight):
        return None


def add_labels(issue_key: str, *labels: str, remove: tuple = ()) -> bool:
    ops = [{"add": lbl} for lbl in labels] + [{"remove": lbl} for lbl in remove]
    try:
        resp = resilient_request("PUT", _issue_url(issue_key), auth=settings.jira_auth, json={"update": {"labels": ops}})
        return resp.ok
    except TransientFailure:
        return False


def transition_once(issue_key: str, transition_id: str, scope_key: str = "") -> bool:
    try:
        with idempotency.idempotent("jira.transition", issue_key, transition_id, scope_key) as g:
            if g.duplicate:
                return True
            key = idempotency.make_key("jira.transition", issue_key, transition_id, scope_key)
            resp = resilient_request("POST", _issue_url(issue_key, "/transitions"), auth=settings.jira_auth,
                                     json={"transition": {"id": transition_id}}, idem_key=key)
            if not resp.ok:
                raise RuntimeError(f"Jira transition HTTP {resp.status_code}: {resp.text[:200]}")
            g.complete({"transition": transition_id})
            return True
    except (TransientFailure, RuntimeError, idempotency.DuplicateInFlight):
        return False


def pause(issue_key: str, alert_body: str, scope_key: str, extra_label: Optional[str] = None) -> None:
    """Contract/quality violation: alert comment + qa-paused label; the issue status is left unchanged."""
    comment_once(issue_key, alert_body, scope_key=f"pause:{scope_key}")
    labels = [settings.paused_label] + ([extra_label] if extra_label else [])
    add_labels(issue_key, *labels)
