"""
TriageAI - LangGraph Jira Triage Agent
AWS Bedrock + LangGraph + MLflow
Author: Ankith Konda
"""
import json
import logging
from typing import TypedDict, Annotated, List, Optional
from datetime import datetime

import mlflow
import boto3
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

logger = logging.getLogger(__name__)


class TriageState(TypedDict):
    ticket_id: str
    ticket_title: str
    ticket_description: str
    ticket_type: str          # bug | feature | story | task
    priority: str             # P0 | P1 | P2 | P3
    severity: str             # critical | high | medium | low
    assigned_team: str
    related_tickets: List[str]
    user_story: Optional[str]
    acceptance_criteria: Optional[List[str]]
    confidence_score: float
    routing_reason: str
    processing_steps: List[str]
    messages: Annotated[List, add_messages]
    created_at: str
    processed_at: Optional[str]


def get_bedrock_llm():
    bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
    return ChatBedrock(
        client=bedrock_client,
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        model_kwargs={"temperature": 0.1, "max_tokens": 2000}
    )


def classify_ticket(state: TriageState) -> TriageState:
    """Node 1: Classify type, severity, priority using CO-STAR + CoT prompting."""
    llm = get_bedrock_llm()
    system_prompt = """
    CONTEXT: Expert software triage specialist at a fintech company.
    OBJECTIVE: Classify the Jira ticket into structured format.
    STYLE: Precise, data-driven, concise.
    TONE: Technical and professional.
    AUDIENCE: Engineering leads and PMs.
    RESPONSE: Return ONLY valid JSON.

    Think step-by-step:
    1. Read title and description
    2. Identify the core problem
    3. Classify ticket type (bug/feature/story/task)
    4. Assign severity (critical/high/medium/low) by user impact
    5. Assign priority (P0/P1/P2/P3) by business urgency

    Return: {"ticket_type":"","severity":"","priority":"","confidence_score":0.0,"reasoning":""}
    """
    user_msg = f"Title: {state['ticket_title']}\nDescription: {state['ticket_description']}"

    with mlflow.start_run(run_name=f"classify_{state['ticket_id']}", nested=True):
        mlflow.log_param("ticket_id", state["ticket_id"])
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_msg)])
        result = json.loads(response.content)
        mlflow.log_metric("confidence_score", result.get("confidence_score", 0))

    state["ticket_type"] = result.get("ticket_type", "task")
    state["severity"] = result.get("severity", "medium")
    state["priority"] = result.get("priority", "P2")
    state["confidence_score"] = result.get("confidence_score", 0.5)
    state["processing_steps"].append(f"classified: {state['ticket_type']} / {state['priority']}")
    return state


def route_ticket(state: TriageState) -> TriageState:
    """Node 2: Route to appropriate engineering team."""
    llm = get_bedrock_llm()
    prompt = f"""
    Route this {state['ticket_type']} ({state['severity']}) ticket:
    Title: {state['ticket_title']}
    Teams: [platform-ai, data-engineering, backend-api, frontend-web, mlops, security, devops, qa]
    Return JSON: {{"assigned_team":"","routing_reason":"","escalate_to_lead":false}}
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    result = json.loads(response.content)
    state["assigned_team"] = result.get("assigned_team", "backend-api")
    state["routing_reason"] = result.get("routing_reason", "")
    state["processing_steps"].append(f"routed to {state['assigned_team']}")
    return state


def enrich_ticket(state: TriageState) -> TriageState:
    """Node 3: Generate user story, acceptance criteria, labels."""
    llm = get_bedrock_llm()
    prompt = f"""
    Enrich this {state['ticket_type']} for {state['assigned_team']} team:
    Title: {state['ticket_title']}
    Description: {state['ticket_description']}
    Return JSON: {{"user_story":"","acceptance_criteria":[],"labels":[]}}
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    result = json.loads(response.content)
    state["user_story"] = result.get("user_story", "")
    state["acceptance_criteria"] = result.get("acceptance_criteria", [])
    state["processed_at"] = datetime.utcnow().isoformat()
    state["processing_steps"].append("enriched with user story and acceptance criteria")
    return state


def should_escalate(state: TriageState) -> str:
    if state["priority"] == "P0" or state["severity"] == "critical":
        return "escalate"
    return "enrich"


def build_triage_graph() -> StateGraph:
    graph = StateGraph(TriageState)
    graph.add_node("classify", classify_ticket)
    graph.add_node("route", route_ticket)
    graph.add_node("enrich", enrich_ticket)
    graph.set_entry_point("classify")
    graph.add_edge("classify", "route")
    graph.add_conditional_edges("route", should_escalate, {
        "escalate": END,
        "enrich": "enrich"
    })
    graph.add_edge("enrich", END)
    return graph.compile()


def run_triage(ticket: dict) -> dict:
    mlflow.set_experiment("triage-ai-agent")
    with mlflow.start_run(run_name=f"triage_{ticket.get('id','unknown')}"):
        mlflow.log_params({"ticket_id": ticket.get("id"), "pipeline": "langgraph_v2"})
        initial_state = TriageState(
            ticket_id=ticket.get("id",""), ticket_title=ticket.get("title",""),
            ticket_description=ticket.get("description",""), ticket_type="",
            priority="", severity="", assigned_team="", related_tickets=[],
            user_story=None, acceptance_criteria=None, confidence_score=0.0,
            routing_reason="", processing_steps=[], messages=[],
            created_at=datetime.utcnow().isoformat(), processed_at=None
        )
        graph = build_triage_graph()
        result = graph.invoke(initial_state)
        mlflow.log_metrics({"confidence_score": result.get("confidence_score", 0)})
        return result
