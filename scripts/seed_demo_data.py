"""Seed demo data for development and testing.
NOTE: All data created by this script is clearly labeled as DEMO data.
"""
import sys
import os
import uuid
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.database import SessionLocal, init_db
from backend.app.services.auth_service import create_user, hash_password
from backend.app.models import (
    User, BusinessProfile, Workflow, Prospect,
    LeadAnalysis, MarketingDraft, Approval, Report, ExecutionLog
)


def seed():
    print("BizPilot AI – Seeding Demo Data")
    print("⚠️  All seeded records are clearly labeled as DEMO data.\n")

    init_db()
    db = SessionLocal()

    try:
        # Demo user
        existing = db.query(User).filter(User.email == "demo@bizpilot.ai").first()
        if existing:
            print("Demo user already exists. Skipping user creation.")
            user = existing
        else:
            user = User(
                id=str(uuid.uuid4()),
                email="demo@bizpilot.ai",
                hashed_password=hash_password("demo1234"),
                full_name="Demo User",
                is_active=True,
            )
            db.add(user)
            db.flush()
            print(f"✅ Created demo user: demo@bizpilot.ai / demo1234")

        # Business profile
        existing_profile = db.query(BusinessProfile).filter(BusinessProfile.user_id == user.id).first()
        if not existing_profile:
            profile = BusinessProfile(
                id=str(uuid.uuid4()),
                user_id=user.id,
                business_name="[DEMO] InnovateTech Solutions",
                description="[DEMO] AI-powered business automation consulting firm.",
                services="AI automation, process optimization, workflow digitization",
                target_industries="Technology, Healthcare, Finance, Logistics",
                target_locations="Bengaluru, Mumbai, Delhi, Hyderabad",
                ideal_customer="Growing startups and SMBs with manual processes",
                tone="professional",
                website="https://example.com",
                business_email="demo@bizpilot.ai",
            )
            db.add(profile)
            print("✅ Created demo business profile")

        # Demo workflow
        wf_id = str(uuid.uuid4())
        workflow = Workflow(
            id=wf_id,
            user_id=user.id,
            title="[DEMO] AI Automation Outreach – Bengaluru Startups",
            instruction="[DEMO] Find 5 startups in Bengaluru that could benefit from AI automation.",
            status="PAUSED",
            current_step="AWAITING_APPROVAL",
            metadata_=json.dumps({"target_count": 5, "min_lead_score": 40}),
            started_at=datetime.now(timezone.utc),
        )
        db.add(workflow)
        db.flush()
        print(f"✅ Created demo workflow: {wf_id[:8]}…")

        # Demo prospects
        prospects_data = [
            {"name": "[DEMO] TechFlow Solutions", "industry": "Technology", "score": 78, "priority": "HIGH"},
            {"name": "[DEMO] HealthBridge Analytics", "industry": "Healthcare Technology", "score": 65, "priority": "HIGH"},
            {"name": "[DEMO] FinPulse Capital", "industry": "Financial Technology", "score": 55, "priority": "MEDIUM"},
            {"name": "[DEMO] LogiTrack Systems", "industry": "Logistics", "score": 42, "priority": "MEDIUM"},
            {"name": "[DEMO] EduSpark Academy", "industry": "Education Technology", "score": 35, "priority": "LOW"},
        ]

        for pd_item in prospects_data:
            existing_p = db.query(Prospect).filter(
                Prospect.user_id == user.id,
                Prospect.company_name == pd_item["name"]
            ).first()
            if existing_p:
                continue

            p_id = str(uuid.uuid4())
            prospect = Prospect(
                id=p_id,
                user_id=user.id,
                workflow_id=wf_id,
                company_name=pd_item["name"],
                website="https://example.com",
                industry=pd_item["industry"],
                description=f"[DEMO DATA] Fictional {pd_item['industry']} company for demonstration purposes.",
                location="Bengaluru, Karnataka, India",
                contact_email="demo@example.com",
                source_urls=json.dumps(["https://example.com/demo"]),
                research_confidence=0.85,
                research_status="researched",
                is_demo=True,
            )
            db.add(prospect)
            db.flush()

            # Lead analysis
            analysis = LeadAnalysis(
                id=str(uuid.uuid4()),
                prospect_id=p_id,
                workflow_id=wf_id,
                lead_score=pd_item["score"],
                priority=pd_item["priority"],
                reasoning=f"[DEMO] Score of {pd_item['score']}/100 based on industry relevance and AI automation potential.",
                potential_needs=json.dumps(["Process automation", "Data analytics", "Workflow optimization"]),
                recommended_approach="[DEMO] Schedule a discovery call to discuss automation opportunities.",
                industry_relevance_score=25,
                business_need_score=20,
                service_compatibility_score=18,
                info_quality_score=8,
                opportunity_score=7,
            )
            db.add(analysis)
            db.flush()

            # Marketing draft
            if pd_item["score"] >= 40:
                draft_id = str(uuid.uuid4())
                draft = MarketingDraft(
                    id=draft_id,
                    prospect_id=p_id,
                    workflow_id=wf_id,
                    user_id=user.id,
                    subject=f"[DEMO DRAFT] AI Automation Partnership with {pd_item['name']}",
                    body=f"""[DEMO EMAIL DRAFT – NOT FOR SENDING]

Dear {pd_item['name']} Team,

I hope this message finds you well. I'm reaching out from [DEMO] InnovateTech Solutions.

We've been working with {pd_item['industry']} companies to streamline their operations through AI-powered automation.

Would you be open to a brief 20-minute call to explore potential synergies?

Best regards,
Demo User
[DEMO] InnovateTech Solutions

---
Score: {pd_item['score']}/100 | Priority: {pd_item['priority']}
This is a DEMO draft generated by BizPilot AI.""",
                    marketing_angle=f"[DEMO] Focus on {pd_item['industry']} efficiency",
                    personalization_notes=f"[DEMO] Personalized for {pd_item['industry']} company in Bengaluru",
                    recipient_email="demo@example.com",
                    status="DRAFT",
                )
                db.add(draft)
                db.flush()

                # Approval request
                import hashlib
                content_hash = hashlib.sha256(
                    f"{draft.subject}{draft.body}{draft.recipient_email}".encode()
                ).hexdigest()

                approval = Approval(
                    id=str(uuid.uuid4()),
                    workflow_id=wf_id,
                    user_id=user.id,
                    draft_id=draft_id,
                    action_type="SEND_EMAIL",
                    action_description=f"[DEMO] Send marketing email to {pd_item['name']}",
                    target_company=pd_item["name"],
                    target_email="demo@example.com",
                    content_hash=content_hash,
                    status="PENDING",
                )
                db.add(approval)

        # Execution logs
        for agent_name, action in [
            ("Research Agent", "research_prospects"),
            ("Analysis Agent", "score_prospects"),
            ("Marketing Agent", "generate_drafts"),
            ("CRM Agent", "save_prospects"),
            ("Approval Agent", "create_approvals"),
        ]:
            log = ExecutionLog(
                id=str(uuid.uuid4()),
                workflow_id=wf_id,
                agent_name=agent_name,
                action=action,
                status="SUCCESS",
                input_summary="[DEMO] Demo instruction",
                output_summary=f"[DEMO] {agent_name} completed successfully",
                duration_ms=350,
            )
            db.add(log)

        db.commit()
        print("\n✅ Demo data seeded successfully!")
        print("\nDemo credentials:")
        print("  Email:    demo@bizpilot.ai")
        print("  Password: demo1234")
        print("\nDemo workflow is PAUSED – log in and visit Approval Center to test approvals.")

    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
