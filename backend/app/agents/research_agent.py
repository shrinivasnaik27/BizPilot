"""Research Agent: Finds and researches business prospects."""
import json, asyncio
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid
from ..services.llm_service import llm_service
from ..config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ProspectResearch(BaseModel):
    company_name: str = Field(..., description="Company name")
    website: str = Field(default="unknown", description="Official website URL")
    industry: str = Field(default="unknown", description="Industry/business category")
    description: str = Field(default="", description="Company description")
    location: str = Field(default="unknown", description="Company location")
    contact_email: str = Field(default="unknown", description="Contact email or unknown")
    contact_phone: str = Field(default="unknown", description="Contact phone or unknown")
    source_urls: List[str] = Field(default_factory=list, description="Research source URLs")
    research_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    research_status: str = Field(default="researched", description="researched/partial/failed")
    is_demo: bool = Field(default=False)

class ResearchResult(BaseModel):
    prospects: List[ProspectResearch]
    total_found: int
    research_provider: str
    research_timestamp: str
    is_demo: bool = False

# Demo dataset - clearly labeled as demo data
DEMO_PROSPECTS = [
    {
        "company_name": "[DEMO] TechFlow Solutions",
        "website": "https://example-techflow.com",
        "industry": "Technology",
        "description": "[DEMO DATA] A fictional technology startup for demonstration purposes. Would benefit from AI-powered process automation.",
        "location": "Bengaluru, Karnataka, India",
        "contact_email": "demo@example.com",
        "source_urls": ["https://example.com/demo"],
        "research_confidence": 0.9,
        "research_status": "researched",
        "is_demo": True
    },
    {
        "company_name": "[DEMO] HealthBridge Analytics",
        "website": "https://example-healthbridge.com",
        "industry": "Healthcare Technology",
        "description": "[DEMO DATA] A fictional healthtech company for demo purposes. Manual data processing creates inefficiencies.",
        "location": "Bengaluru, Karnataka, India",
        "contact_email": "demo@example.com",
        "source_urls": ["https://example.com/demo"],
        "research_confidence": 0.85,
        "research_status": "researched",
        "is_demo": True
    },
    {
        "company_name": "[DEMO] FinPulse Capital",
        "website": "https://example-finpulse.com",
        "industry": "Financial Technology",
        "description": "[DEMO DATA] A fictional fintech startup for demo purposes. Customer onboarding process is manual.",
        "location": "Bengaluru, Karnataka, India",
        "contact_email": "demo@example.com",
        "source_urls": ["https://example.com/demo"],
        "research_confidence": 0.8,
        "research_status": "researched",
        "is_demo": True
    },
    {
        "company_name": "[DEMO] LogiTrack Systems",
        "website": "https://example-logitrack.com",
        "industry": "Logistics & Supply Chain",
        "description": "[DEMO DATA] A fictional logistics company for demo. Route optimization done manually.",
        "location": "Bengaluru, Karnataka, India",
        "contact_email": "demo@example.com",
        "source_urls": ["https://example.com/demo"],
        "research_confidence": 0.75,
        "research_status": "researched",
        "is_demo": True
    },
    {
        "company_name": "[DEMO] EduSpark Academy",
        "website": "https://example-eduspark.com",
        "industry": "Education Technology",
        "description": "[DEMO DATA] A fictional edtech startup for demo. Student progress tracking done manually.",
        "location": "Bengaluru, Karnataka, India",
        "contact_email": "demo@example.com",
        "source_urls": ["https://example.com/demo"],
        "research_confidence": 0.78,
        "research_status": "researched",
        "is_demo": True
    },
]

class ResearchAgent:
    def __init__(self):
        self.settings = get_settings()
        self.agent_name = "Research Agent"
    
    async def research(self, instruction: str, target_count: int = 5, existing_companies: List[str] = None) -> ResearchResult:
        """Research prospects based on the instruction."""
        logger.info(f"Research Agent starting: {instruction[:100]}...")
        existing_companies = existing_companies or []
        
        if llm_service.is_demo_mode or self.settings.research_provider == "mock":
            return await self._demo_research(instruction, target_count, existing_companies)
        
        return await self._llm_research(instruction, target_count, existing_companies)
    
    async def _demo_research(self, instruction: str, target_count: int, existing_companies: List[str]) -> ResearchResult:
        """Return clearly labeled demo research results."""
        logger.info("Research Agent: Using DEMO mode - returning mock prospects")
        await asyncio.sleep(0.5)  # Simulate research time
        
        prospects = []
        for p in DEMO_PROSPECTS[:target_count]:
            if p["company_name"] not in existing_companies:
                prospects.append(ProspectResearch(**p))
        
        return ResearchResult(
            prospects=prospects,
            total_found=len(prospects),
            research_provider="DEMO (Mock Data - Configure RESEARCH_PROVIDER for real data)",
            research_timestamp=datetime.now(timezone.utc).isoformat(),
            is_demo=True
        )
    
    async def _llm_research(self, instruction: str, target_count: int, existing_companies: List[str]) -> ResearchResult:
        """Use LLM + search API to research real prospects."""
        system_prompt = """You are a business research specialist. Your job is to identify and research real companies that match the user's criteria. 
        
CRITICAL RULES:
- Only suggest real, verifiable companies
- Mark any uncertain information as "unknown" 
- Never fabricate contact details
- Provide source URLs for verification
- Avoid duplicate companies

Return a JSON array of company objects with fields: company_name, website, industry, description, location, contact_email, source_urls, research_confidence, research_status"""

        user_prompt = f"""Research task: {instruction}

Find {target_count} companies. Already found (skip these): {existing_companies}

For each company provide:
- company_name: Real company name
- website: Official website or "unknown"
- industry: Business category
- description: What they do (2-3 sentences)
- location: City, State, Country
- contact_email: If publicly available, else "unknown"  
- source_urls: List of URLs where you found this info
- research_confidence: 0.0-1.0 (how confident in accuracy)
- research_status: "researched", "partial", or "failed"

Return JSON array only."""

        try:
            response = await llm_service.generate(system_prompt, user_prompt)
            # Parse the JSON response
            if isinstance(response, str):
                # Extract JSON from response
                import re
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = json.loads(response)
            else:
                data = response
            
            prospects = [ProspectResearch(**p) for p in data if p.get("company_name")]
            return ResearchResult(
                prospects=prospects,
                total_found=len(prospects),
                research_provider="Groq LLM",
                research_timestamp=datetime.now(timezone.utc).isoformat(),
                is_demo=False
            )
        except Exception as e:
            logger.error(f"LLM research failed: {e}")
            # Fallback to demo
            return await self._demo_research(instruction, target_count, existing_companies)

research_agent = ResearchAgent()
