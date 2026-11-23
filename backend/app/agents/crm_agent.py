"""CRM Agent: Manages prospects, analyses, and drafts in the database."""
import uuid, json
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..models.prospect import Prospect
from ..models.lead_analysis import LeadAnalysis
from ..models.marketing_draft import MarketingDraft
from ..agents.research_agent import ProspectResearch
from ..agents.analysis_agent import LeadScore
from ..agents.marketing_agent import EmailDraft
from ..utils.logger import get_logger

logger = get_logger(__name__)

class CRMResult:
    def __init__(self):
        self.prospects_saved = 0
        self.prospects_updated = 0
        self.analyses_saved = 0
        self.drafts_saved = 0
        self.errors = []
        self.prospect_ids = []
        self.draft_ids = []

class CRMAgent:
    def __init__(self):
        self.agent_name = "CRM Agent"
    
    def save_prospects(self, db: Session, prospects: List[ProspectResearch], scores: List[LeadScore], drafts: List[EmailDraft], workflow_id: str, user_id: str) -> CRMResult:
        """Save all prospect data to the database."""
        result = CRMResult()
        score_map = {s.company_name: s for s in scores}
        draft_map = {d.company_name: d for d in drafts}
        
        for prospect_data in prospects:
            try:
                # Check for existing prospect
                existing = db.query(Prospect).filter(
                    Prospect.user_id == user_id,
                    Prospect.company_name == prospect_data.company_name
                ).first()
                
                if existing:
                    # Update existing
                    existing.website = prospect_data.website
                    existing.industry = prospect_data.industry
                    existing.description = prospect_data.description
                    existing.location = prospect_data.location
                    existing.research_confidence = prospect_data.research_confidence
                    existing.research_status = prospect_data.research_status
                    existing.source_urls = json.dumps(prospect_data.source_urls)
                    existing.updated_at = datetime.now(timezone.utc)
                    prospect_id = existing.id
                    result.prospects_updated += 1
                else:
                    # Create new
                    new_prospect = Prospect(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        workflow_id=workflow_id,
                        company_name=prospect_data.company_name,
                        website=prospect_data.website,
                        industry=prospect_data.industry,
                        description=prospect_data.description,
                        location=prospect_data.location,
                        contact_email=prospect_data.contact_email,
                        source_urls=json.dumps(prospect_data.source_urls),
                        research_confidence=prospect_data.research_confidence,
                        research_status=prospect_data.research_status,
                        is_demo=prospect_data.is_demo,
                    )
                    db.add(new_prospect)
                    db.flush()
                    prospect_id = new_prospect.id
                    result.prospects_saved += 1
                
                result.prospect_ids.append(prospect_id)
                
                # Save lead analysis
                score = score_map.get(prospect_data.company_name)
                if score:
                    existing_analysis = db.query(LeadAnalysis).filter(
                        LeadAnalysis.prospect_id == prospect_id
                    ).first()
                    
                    if not existing_analysis:
                        analysis = LeadAnalysis(
                            id=str(uuid.uuid4()),
                            prospect_id=prospect_id,
                            workflow_id=workflow_id,
                            lead_score=score.lead_score,
                            priority=score.priority,
                            reasoning=score.reasoning,
                            potential_needs=json.dumps(score.potential_needs),
                            recommended_approach=score.recommended_approach,
                            industry_relevance_score=score.industry_relevance_score,
                            business_need_score=score.business_need_score,
                            service_compatibility_score=score.service_compatibility_score,
                            info_quality_score=score.info_quality_score,
                            opportunity_score=score.opportunity_score,
                        )
                        db.add(analysis)
                        result.analyses_saved += 1
                
                # Save marketing draft
                draft = draft_map.get(prospect_data.company_name)
                if draft:
                    new_draft = MarketingDraft(
                        id=str(uuid.uuid4()),
                        prospect_id=prospect_id,
                        workflow_id=workflow_id,
                        user_id=user_id,
                        subject=draft.subject,
                        body=draft.body,
                        marketing_angle=draft.marketing_angle,
                        personalization_notes=draft.personalization_notes,
                        recipient_email=draft.recipient_email,
                        status="DRAFT",
                    )
                    db.add(new_draft)
                    db.flush()
                    result.draft_ids.append(new_draft.id)
                    result.drafts_saved += 1
                    
            except IntegrityError as e:
                db.rollback()
                logger.error(f"CRM integrity error for {prospect_data.company_name}: {e}")
                result.errors.append(f"Duplicate: {prospect_data.company_name}")
            except Exception as e:
                logger.error(f"CRM save error for {prospect_data.company_name}: {e}")
                result.errors.append(str(e))
        
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"CRM commit failed: {e}")
            result.errors.append(f"Commit failed: {str(e)}")
        
        logger.info(f"CRM Agent: Saved {result.prospects_saved} new, updated {result.prospects_updated}, {result.drafts_saved} drafts")
        return result

crm_agent = CRMAgent()
