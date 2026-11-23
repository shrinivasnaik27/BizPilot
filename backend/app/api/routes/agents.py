"""Agent status routes."""
from fastapi import APIRouter, Depends
from ...api.dependencies import get_current_user
from ...services.llm_service import llm_service
from ...config import get_settings
from ...models.user import User

router = APIRouter(prefix="/api/agents", tags=["Agents"])

AGENTS_INFO = [
    {"name": "Research Agent", "purpose": "Find and research business prospects", "id": "research"},
    {"name": "Analysis Agent", "purpose": "Score and rank prospects by business potential", "id": "analysis"},
    {"name": "Marketing Agent", "purpose": "Generate personalized email drafts", "id": "marketing"},
    {"name": "CRM Agent", "purpose": "Save prospects and drafts to database", "id": "crm"},
    {"name": "Approval Agent", "purpose": "Human-in-the-loop approval management", "id": "approval"},
    {"name": "Reporting Agent", "purpose": "Generate business intelligence reports", "id": "reporting"},
]


@router.get("")
async def list_agents(current_user: User = Depends(get_current_user)):
    settings = get_settings()
    return {
        "agents": AGENTS_INFO,
        "llm_status": llm_service.get_status(),
        "demo_mode": settings.demo_mode,
    }


@router.get("/status")
async def agent_system_status(current_user: User = Depends(get_current_user)):
    settings = get_settings()
    return {
        "system": "operational",
        "demo_mode": settings.demo_mode,
        "llm_configured": not llm_service.is_demo_mode,
        "research_provider": settings.research_provider,
        "email_configured": bool(settings.smtp_host),
        "agent_count": len(AGENTS_INFO),
    }
