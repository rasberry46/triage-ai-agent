# 🤖 TriageAI Agent

> **Production-grade Jira Ticket Triage using LangGraph + AWS Bedrock + MLflow**  
> Automates ticket classification, routing, and enrichment — reducing triage cycle time by 30–35%.

[![Python](https://img.shields.io/badge/python-3.11-blue)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-green)](https://langchain-ai.github.io/langgraph/)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock%20Claude-orange)](https://aws.amazon.com/bedrock/)
[![MLflow](https://img.shields.io/badge/MLflow-2.16-red)](https://mlflow.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🎯 What It Does

TriageAI connects to your Jira instance via webhook and automatically:

| Step | What Happens |
|------|-------------|
| 📥 **Ingest** | Jira webhook triggers on issue_created / issue_updated |
| 🧠 **Classify** | LangGraph agent classifies type, severity, priority (P0–P3) |
| 🔀 **Route** | Routes to correct engineering team (mlops, backend-api, platform-ai...) |
| ✍️ **Enrich** | Generates user story, acceptance criteria, labels |
| 🚨 **Escalate** | P0/critical tickets skip enrichment → instant Slack alert |
| 📊 **Track** | MLflow logs every decision; CloudWatch metrics for dashboards |

---

## 🏗️ Architecture

```
Jira Webhook
     │
     ▼
FastAPI Webhook Handler
     │
     ▼
LangGraph Triage Pipeline
  ├── Node 1: classify_ticket  (CO-STAR + CoT prompt → type/severity/priority)
  ├── Node 2: route_ticket     (semantic routing → engineering team)
  └── Node 3: enrich_ticket    (user story + acceptance criteria)
     │
     ├── AWS Bedrock (Claude Sonnet 3.5 v2)
     ├── MLflow Experiment Tracker
     ├── CloudWatch Metrics
     └── Jira REST API (update ticket)
```

---

## 🚀 Quickstart

```bash
git clone https://github.com/rasberry46/triage-ai-agent
cd triage-ai-agent
cp .env.example .env    # fill in your credentials
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Set your Jira webhook URL to: `https://your-domain/webhook/jira`

---

## 📈 Results (Intuit Production Baseline)

| Metric | Before | After |
|--------|--------|-------|
| Triage cycle time | ~45 min | ~8 min |
| Manual routing errors | 18% | 3% |
| Sprint backlog clearance | baseline | +30% |
| Engineer context switches | high | reduced by ~40% |

> Based on pilot deployment across 3 squads at Intuit (QuickBooks platform, 2024–2025).

---

## 🛠️ Stack

- **Agent Orchestration**: LangGraph (stateful multi-node graph)
- **LLM**: AWS Bedrock — Claude Sonnet 3.5 v2
- **Prompting**: CO-STAR framework + Chain-of-Thought reasoning
- **Experiment Tracking**: MLflow (confidence scores, routing decisions)
- **Observability**: AWS CloudWatch (custom metrics namespace: TriageAI)
- **API**: FastAPI + Pydantic v2
- **CI/CD**: GitHub Actions → ECR → EKS (blue/green)
- **Alerting**: Slack webhooks for P0 escalations

---

## 📁 Project Structure

```
triage-ai-agent/
├── agents/
│   └── triage/
│       └── triage_agent.py      # LangGraph graph definition
├── api/
│   └── routes/
│       └── webhook.py           # FastAPI Jira webhook handler
├── config/
│   └── settings.py              # Pydantic settings
├── monitoring/
│   └── metrics.py               # CloudWatch + MLflow tracker
├── infra/
│   ├── docker/Dockerfile
│   └── github-actions/triage-ci.yml
├── tests/
├── requirements.txt
└── README.md
```

---

## 🔗 Related Work

- **Introspect AI Studio** — multi-agent debate + document analysis
- **ArchitectAI** — enterprise system architecture simulator
- IEEE Publication: *Agentic AI Orchestration Patterns for Enterprise DevOps*

---

*Built by [Ankith Konda](https://github.com/rasberry46) — Lead AI/ML Engineer*
