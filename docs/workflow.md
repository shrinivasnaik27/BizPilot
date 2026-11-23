# BizPilot AI – Workflow Documentation

## End-to-End Workflow

### User Provides Instruction

The user enters a natural-language instruction in the AI Assistant page, e.g.:

```
Find 10 healthcare startups in Bengaluru that need AI automation.
Research their business, evaluate potential, generate marketing emails,
save to CRM, and produce a report.
```

### Orchestrator Creates Workflow

A `Workflow` record is created in the database with status `PENDING`. The orchestrator receives the instruction and builds initial `WorkflowState`.

### Research Phase

The Research Agent:
1. Parses the instruction to identify target criteria (industry, location, count)
2. Queries the configured research provider (mock or real API)
3. Returns structured `ProspectResearch` objects
4. Avoids duplicate companies (checks existing list)

### Analysis Phase

The Analysis Agent:
1. Receives all researched prospects
2. Scores each on 100-point scale:
   - Industry relevance: 0–30 points
   - Business need: 0–25 points
   - Service compatibility: 0–25 points
   - Information quality: 0–10 points
   - Business opportunity: 0–10 points
3. Assigns priority: HIGH (≥65), MEDIUM (40–64), LOW (<40)

### Marketing Phase

The Marketing Agent:
1. Filters prospects with score ≥ min_lead_score (default: 40)
2. Reads user's business profile for personalization context
3. Generates personalized email drafts
4. Each draft includes: subject, body, marketing angle, personalization notes

### CRM Phase

The CRM Agent:
1. Saves all prospects to database (upserts to avoid duplicates)
2. Saves lead analyses
3. Saves marketing drafts
4. Returns IDs for all saved records

### Approval Phase (PAUSED)

The Approval Agent:
1. Creates a `PENDING` approval for each email draft
2. Workflow status becomes `PAUSED` / `AWAITING_APPROVAL`
3. User is notified in the Approval Center
4. **Workflow does not proceed until user takes action**

### Human Review

User in Approval Center:
- Previews full email draft
- Optionally edits subject or body
- Approves (APPROVED) or Rejects (REJECTED)
- Backend verifies: content hash, approval status, user ownership

### Resume & Reporting

After approvals, user clicks "Resume Workflow":
1. Reporting Agent generates comprehensive report
2. Workflow status becomes `COMPLETED`
3. Report available in Reports page
4. CSV export available

## Workflow States

| State | Description |
|-------|-------------|
| PENDING | Created, not yet started |
| RUNNING | Agents actively executing |
| PAUSED | Waiting for human approval |
| COMPLETED | All steps finished successfully |
| FAILED | An agent encountered an unrecoverable error |
| CANCELLED | User manually cancelled |

## Resuming After Pause

The workflow state is persisted in the `Workflow.metadata_` JSON column. When resumed, the orchestrator reads this state and runs only the remaining steps (Reporting) without repeating research or creating duplicate CRM records.
