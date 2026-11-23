"""Analysis Agent: Scores and ranks prospects by business potential."""
import json, asyncio
from typing import List
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from ..services.llm_service import llm_service
from ..agents.research_agent import ProspectResearch
from ..utils.logger import get_logger

logger = get_logger(__name__)

class LeadScore(BaseModel):
    company_name: str
    lead_score: int = Field(..., ge=0, le=100)
    priority: str = Field(..., description="HIGH/MEDIUM/LOW")
    reasoning: str
    potential_needs: List[str] = Field(default_factory=list)
    recommended_approach: str = Field(default="")
    industry_relevance_score: int = Field(default=0, ge=0, le=30)
    business_need_score: int = Field(default=0, ge=0, le=25)
    service_compatibility_score: int = Field(default=0, ge=0, le=25)
    info_quality_score: int = Field(default=0, ge=0, le=10)
    opportunity_score: int = Field(default=0, ge=0, le=10)

class AnalysisResult(BaseModel):
    scored_prospects: List[LeadScore]
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    analysis_timestamp: str
    is_demo: bool = False

class AnalysisAgent:
    def __init__(self):
        self.agent_name = "Analysis Agent"
    
    def _calculate_demo_score(self, prospect: ProspectResearch, business_context: str) -> LeadScore:
        """Calculate a deterministic demo score for a prospect."""
        # Simple scoring based on industry keywords
        industry_keywords = ["tech", "ai", "software", "data", "digital", "automation", "analytics"]
        industry_lower = prospect.industry.lower()
        
        industry_score = 20 if any(kw in industry_lower for kw in industry_keywords) else 12
        need_score = 20 if prospect.research_confidence > 0.7 else 15
        compat_score = 18
        info_score = 8 if prospect.contact_email != "unknown" else 5
        opp_score = 7
        
        total = industry_score + need_score + compat_score + info_score + opp_score
        
        priority = "HIGH" if total >= 65 else "MEDIUM" if total >= 40 else "LOW"
        
        return LeadScore(
            company_name=prospect.company_name,
            lead_score=total,
            priority=priority,
            reasoning=f"[DEMO ANALYSIS] Score based on industry relevance ({industry_score}/30), estimated business need ({need_score}/25), service compatibility ({compat_score}/25), information quality ({info_score}/10), business opportunity ({opp_score}/10).",
            potential_needs=["Process automation", "Data analytics", "Workflow optimization"],
            recommended_approach="[DEMO] Schedule discovery call to understand current pain points and automation opportunities.",
            industry_relevance_score=industry_score,
            business_need_score=need_score,
            service_compatibility_score=compat_score,
            info_quality_score=info_score,
            opportunity_score=opp_score
        )
    
    async def analyze(self, prospects: List[ProspectResearch], business_context: str, instruction: str) -> AnalysisResult:
        """Analyze and score all prospects."""
        logger.info(f"Analysis Agent: Scoring {len(prospects)} prospects")
        
        scored = []
        
        if llm_service.is_demo_mode:
            await asyncio.sleep(0.3)
            for prospect in prospects:
                score = self._calculate_demo_score(prospect, business_context)
                scored.append(score)
        else:
            for prospect in prospects:
                score = await self._llm_analyze(prospect, business_context, instruction)
                scored.append(score)
        
        # Sort by score descending
        scored.sort(key=lambda x: x.lead_score, reverse=True)
        
        high = sum(1 for s in scored if s.priority == "HIGH")
        medium = sum(1 for s in scored if s.priority == "MEDIUM")
        low = sum(1 for s in scored if s.priority == "LOW")
        
        return AnalysisResult(
            scored_prospects=scored,
            high_priority_count=high,
            medium_priority_count=medium,
            low_priority_count=low,
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            is_demo=llm_service.is_demo_mode
        )
    
    async def _llm_analyze(self, prospect: ProspectResearch, business_context: str, instruction: str) -> LeadScore:
        """Use LLM to analyze a single prospect."""
        system_prompt = """You are a business development analyst. Score prospects for their potential to benefit from the offered services.

Scoring criteria (total 100 points):
- Industry relevance: 0-30 points
- Business need: 0-25 points  
- Service compatibility: 0-25 points
- Information quality: 0-10 points
- Business opportunity: 0-10 points

Be transparent about your reasoning. Never fabricate information."""

        user_prompt = f"""Business context: {business_context}
Original instruction: {instruction}

Prospect to analyze:
Company: {prospect.company_name}
Industry: {prospect.industry}
Description: {prospect.description}
Location: {prospect.location}
Research confidence: {prospect.research_confidence}
Contact available: {prospect.contact_email != 'unknown'}

Provide scores and analysis as JSON with fields:
company_name, lead_score (0-100), priority (HIGH/MEDIUM/LOW), reasoning, potential_needs (array), recommended_approach, industry_relevance_score, business_need_score, service_compatibility_score, info_quality_score, opportunity_score"""

        try:
            response = await llm_service.generate(system_prompt, user_prompt)
            if isinstance(response, str):
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                data = json.loads(json_match.group() if json_match else response)
            else:
                data = response
            data["company_name"] = prospect.company_name
            return LeadScore(**data)
        except Exception as e:
            logger.error(f"LLM analysis failed for {prospect.company_name}: {e}")
            return self._calculate_demo_score(prospect, business_context)

analysis_agent = AnalysisAgent()
