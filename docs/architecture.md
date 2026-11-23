# BizPilot AI – System Architecture

## Overview

BizPilot AI is a layered multi-agent system where a central LangGraph orchestrator coordinates six specialized agents through a shared workflow state machine.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                          │
│   Streamlit Dashboard (9 Pages)  ←→  API Client Service        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP REST (JWT)
┌──────────────────────────▼──────────────────────────────────────┐
│                        BACKEND LAYER                           │
│   FastAPI Application                                          │
│   ├── Auth Routes (/api/auth/*)                               │
│   ├── Workflow Routes (/api/workflows/*)                      │
│   ├── Prospect Routes (/api/prospects/*)                      │
│   ├── Approval Routes (/api/approvals/*)                      │
│   ├── Marketing Routes (/api/marketing/*)                     │
│   ├── Report Routes (/api/reports/*)                          │
│   └── Agent Routes (/api/agents/*)                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    ORCHESTRATION LAYER                         │
│   LangGraph State Machine                                      │
│   WorkflowState (TypedDict)                                    │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │ research → analysis → marketing → crm → approval        │  │
│   │                                           ↓             │  │
│   │                                    [PAUSED - wait]      │  │
│   │                                           ↓             │  │
│   │                                       reporting → END   │  │
│   └─────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                       AGENT LAYER                              │
│   Research Agent  │  Analysis Agent  │  Marketing Agent        │
│   CRM Agent       │  Approval Agent  │  Reporting Agent        │
│                           │                                    │
│                   LLM Service (Groq / Demo)                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                        DATA LAYER                              │
│   SQLAlchemy ORM                                               │
│   SQLite (dev) / PostgreSQL (prod)                             │
│   Tables: users, workflows, prospects, lead_analyses,          │
│           marketing_drafts, approvals, reports, execution_logs │
└─────────────────────────────────────────────────────────────────┘
```

## Workflow State Machine

```
PENDING
  │
  ▼ (start_workflow called)
RUNNING
  │
  ├── research_node → analysis_node → marketing_node → crm_node
  │
  ├── [drafts exist?] → approval_node
  │                         │
  │                         ▼
  │                      PAUSED (AWAITING_APPROVAL)
  │                         │
  │                    [user approves]
  │                         │
  │                         ▼
  │                      RUNNING (resumed)
  │                         │
  └── reporting_node
           │
           ▼
        COMPLETED
  │
  └── [any error] → FAILED
```

## Security Architecture

- JWT tokens (HS256) with 24-hour expiry
- bcrypt password hashing
- User-scoped data access (every query filters by user_id)
- Backend-side approval verification (independent of UI)
- SHA-256 content hash guards against post-approval content changes
- Audit log for all approval decisions
