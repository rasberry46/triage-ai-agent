"""
FastAPI webhook endpoint — receives Jira events and triggers triage pipeline.
"""
import hmac, hashlib, logging
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from agents.triage.triage_agent import run_triage
from monitoring.metrics import MetricsTracker
from config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class JiraWebhookPayload(BaseModel):
    webhookEvent: str
    issue: dict
    user: Optional[dict] = None


async def verify_jira_signature(request: Request) -> bool:
    signature = request.headers.get("X-Hub-Signature")
    if not signature:
        return False
    body = await request.body()
    expected = "sha256=" + hmac.new(
        settings.JIRA_WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


async def process_ticket_background(ticket_data: dict):
    """Run triage asynchronously after webhook response."""
    try:
        result = run_triage(ticket_data)
        logger.info(f"Triage complete: {ticket_data['id']} -> {result.get('assigned_team')}")
        MetricsTracker.push_cloudwatch(result)
    except Exception as e:
        logger.error(f"Triage failed for {ticket_data.get('id')}: {e}")
        MetricsTracker.record_failure(ticket_data.get("id"), str(e))


@router.post("/webhook/jira")
async def jira_webhook(request: Request, background_tasks: BackgroundTasks):
    if settings.VERIFY_SIGNATURES and not await verify_jira_signature(request):
        raise HTTPException(status_code=401, detail="Invalid signature")

    body = await request.json()
    event = body.get("webhookEvent", "")

    if event not in ["jira:issue_created", "jira:issue_updated"]:
        return {"status": "ignored", "event": event}

    issue = body.get("issue", {})
    ticket_data = {
        "id": issue.get("key", ""),
        "title": issue.get("fields", {}).get("summary", ""),
        "description": issue.get("fields", {}).get("description", ""),
        "reporter": issue.get("fields", {}).get("reporter", {}).get("displayName", ""),
        "project": issue.get("fields", {}).get("project", {}).get("key", ""),
    }

    background_tasks.add_task(process_ticket_background, ticket_data)
    return {"status": "accepted", "ticket_id": ticket_data["id"]}
