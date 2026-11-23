"""BizPilot AI – Automated Test Suite."""
import pytest
import json
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use in-memory SQLite for tests
TEST_DB_URL = "sqlite:///./test_bizpilot.db"

import os
os.environ.setdefault("DATABASE_URL", TEST_DB_URL)
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-characters-long")
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("APP_ENV", "testing")

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, BusinessProfile, Workflow, Prospect, LeadAnalysis, MarketingDraft, Approval, Report, ExecutionLog

# Test database setup
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_bizpilot.db"):
        os.remove("test_bizpilot.db")


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(client):
    """Register and return a test user with token."""
    email = f"test_{uuid.uuid4().hex[:8]}@test.com"
    response = client.post("/api/auth/register", json={
        "email": email,
        "password": "testpass123",
        "full_name": "Test User"
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def auth_headers(test_user):
    return {"Authorization": f"Bearer {test_user['access_token']}"}


# ── Health Tests ───────────────────────────────────────────────────────────────

class TestHealth:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "BizPilot AI"
        assert data["status"] == "operational"

    def test_health_endpoint(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert "database" in data

    def test_docs_accessible(self, client):
        r = client.get("/docs")
        assert r.status_code == 200


# ── Auth Tests ─────────────────────────────────────────────────────────────────

class TestAuth:
    def test_register_success(self, client):
        r = client.post("/api/auth/register", json={
            "email": f"newuser_{uuid.uuid4().hex[:6]}@test.com",
            "password": "password123",
            "full_name": "New User"
        })
        assert r.status_code == 201
        data = r.json()
        assert "access_token" in data
        assert data["user"]["email"] is not None

    def test_register_weak_password(self, client):
        r = client.post("/api/auth/register", json={
            "email": "weak@test.com",
            "password": "short"
        })
        assert r.status_code == 422  # Validation error

    def test_register_duplicate_email(self, client, test_user):
        email = test_user["user"]["email"]
        r = client.post("/api/auth/register", json={"email": email, "password": "password123"})
        assert r.status_code == 400

    def test_login_success(self, client, test_user):
        email = test_user["user"]["email"]
        r = client.post("/api/auth/login", json={"email": email, "password": "testpass123"})
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_wrong_password(self, client, test_user):
        email = test_user["user"]["email"]
        r = client.post("/api/auth/login", json={"email": email, "password": "wrongpassword"})
        assert r.status_code == 401

    def test_me_endpoint(self, client, auth_headers, test_user):
        r = client.get("/api/auth/me", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["email"] == test_user["user"]["email"]

    def test_protected_endpoint_no_token(self, client):
        r = client.get("/api/prospects")
        assert r.status_code == 401


# ── Business Profile Tests ─────────────────────────────────────────────────────

class TestBusinessProfile:
    def test_create_profile(self, client, auth_headers):
        r = client.post("/api/business/profile", json={
            "business_name": "Test Company",
            "description": "A test business",
            "services": "AI automation",
        }, headers=auth_headers)
        assert r.status_code == 201
        assert r.json()["business_name"] == "Test Company"

    def test_get_profile(self, client, auth_headers):
        # Create first
        client.post("/api/business/profile", json={
            "business_name": "My Business",
            "description": "Description",
            "services": "Services",
        }, headers=auth_headers)
        r = client.get("/api/business/profile", headers=auth_headers)
        assert r.status_code == 200

    def test_update_profile(self, client, auth_headers):
        client.post("/api/business/profile", json={
            "business_name": "Original Name",
            "description": "Desc",
            "services": "Services",
        }, headers=auth_headers)
        r = client.put("/api/business/profile", json={
            "business_name": "Updated Name",
            "description": "New desc",
            "services": "Updated services",
        }, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["business_name"] == "Updated Name"


# ── Prospect Tests ─────────────────────────────────────────────────────────────

class TestProspects:
    def test_create_prospect(self, client, auth_headers):
        r = client.post("/api/prospects", json={
            "company_name": f"TestCo {uuid.uuid4().hex[:6]}",
            "industry": "Technology",
            "location": "Bengaluru",
        }, headers=auth_headers)
        assert r.status_code == 201
        assert "id" in r.json()

    def test_duplicate_prospect_rejected(self, client, auth_headers):
        name = f"UniqueCompany {uuid.uuid4().hex[:8]}"
        client.post("/api/prospects", json={"company_name": name}, headers=auth_headers)
        r = client.post("/api/prospects", json={"company_name": name}, headers=auth_headers)
        assert r.status_code == 400

    def test_list_prospects(self, client, auth_headers):
        r = client.get("/api/prospects", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_update_prospect(self, client, auth_headers):
        create_r = client.post("/api/prospects", json={
            "company_name": f"ToUpdate {uuid.uuid4().hex[:6]}"
        }, headers=auth_headers)
        pid = create_r.json()["id"]
        r = client.put(f"/api/prospects/{pid}", json={"industry": "Updated Industry"}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["industry"] == "Updated Industry"

    def test_delete_prospect(self, client, auth_headers):
        create_r = client.post("/api/prospects", json={
            "company_name": f"ToDelete {uuid.uuid4().hex[:6]}"
        }, headers=auth_headers)
        pid = create_r.json()["id"]
        r = client.delete(f"/api/prospects/{pid}", headers=auth_headers)
        assert r.status_code == 200
        # Verify deleted
        get_r = client.get(f"/api/prospects/{pid}", headers=auth_headers)
        assert get_r.status_code == 404

    def test_prospect_search(self, client, auth_headers):
        unique_name = f"SearchableCompany_{uuid.uuid4().hex[:6]}"
        client.post("/api/prospects", json={"company_name": unique_name}, headers=auth_headers)
        r = client.get(f"/api/prospects?search={unique_name[:10]}", headers=auth_headers)
        assert r.status_code == 200
        results = r.json()
        assert any(unique_name in p["company_name"] for p in results)


# ── Workflow Tests ─────────────────────────────────────────────────────────────

class TestWorkflows:
    def test_create_workflow(self, client, auth_headers):
        r = client.post("/api/workflows", json={
            "instruction": "Find 3 tech startups in Bengaluru that need AI automation",
            "target_count": 3,
            "min_lead_score": 40,
        }, headers=auth_headers)
        assert r.status_code == 201
        data = r.json()
        assert "id" in data
        assert data["status"] in ("PENDING", "RUNNING")

    def test_workflow_instruction_too_short(self, client, auth_headers):
        r = client.post("/api/workflows", json={"instruction": "Too short"}, headers=auth_headers)
        assert r.status_code == 422

    def test_list_workflows(self, client, auth_headers):
        r = client.get("/api/workflows", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_workflow(self, client, auth_headers):
        create_r = client.post("/api/workflows", json={
            "instruction": "Find healthcare startups in Mumbai that need automation help",
            "target_count": 2,
        }, headers=auth_headers)
        wf_id = create_r.json()["id"]
        r = client.get(f"/api/workflows/{wf_id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == wf_id

    def test_cancel_workflow(self, client, auth_headers, db):
        create_r = client.post("/api/workflows", json={
            "instruction": "Find fintech companies in Delhi that want automation",
            "target_count": 2,
        }, headers=auth_headers)
        wf_id = create_r.json()["id"]
        r = client.post(f"/api/workflows/{wf_id}/cancel", headers=auth_headers)
        assert r.status_code == 200
        get_r = client.get(f"/api/workflows/{wf_id}", headers=auth_headers)
        assert get_r.json()["status"] == "CANCELLED"


# ── Approval Tests ─────────────────────────────────────────────────────────────

class TestApprovals:
    def _setup_approval(self, client, auth_headers, db, user_id):
        """Create the minimum DB objects needed for an approval test."""
        wf_id = str(uuid.uuid4())
        wf = Workflow(id=wf_id, user_id=user_id, title="Test", instruction="Test workflow instruction here",
                      status="PAUSED", current_step="AWAITING_APPROVAL")
        db.add(wf)
        db.flush()

        p_id = str(uuid.uuid4())
        p = Prospect(id=p_id, user_id=user_id, workflow_id=wf_id, company_name=f"TestCo {uuid.uuid4().hex[:6]}")
        db.add(p)
        db.flush()

        d_id = str(uuid.uuid4())
        d = MarketingDraft(id=d_id, prospect_id=p_id, workflow_id=wf_id, user_id=user_id,
                           subject="Test Subject", body="Test body content for approval testing",
                           status="DRAFT", recipient_email="test@example.com")
        db.add(d)
        db.flush()

        import hashlib
        content_hash = hashlib.sha256(f"{d.subject}{d.body}{d.recipient_email}".encode()).hexdigest()

        a_id = str(uuid.uuid4())
        a = Approval(id=a_id, workflow_id=wf_id, user_id=user_id, draft_id=d_id,
                     action_type="SEND_EMAIL", action_description="Send test email",
                     target_company="TestCo", target_email="test@example.com",
                     content_hash=content_hash, status="PENDING")
        db.add(a)
        db.commit()
        return a_id, d_id

    def test_list_approvals(self, client, auth_headers):
        r = client.get("/api/approvals", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_approve_action(self, client, auth_headers, db, test_user):
        user_id = test_user["user"]["id"]
        a_id, d_id = self._setup_approval(client, auth_headers, db, user_id)
        r = client.post(f"/api/approvals/{a_id}/approve", json={}, headers=auth_headers)
        assert r.status_code == 200
        assert "approved" in r.json()["message"].lower()

    def test_reject_action(self, client, auth_headers, db, test_user):
        user_id = test_user["user"]["id"]
        a_id, d_id = self._setup_approval(client, auth_headers, db, user_id)
        r = client.post(f"/api/approvals/{a_id}/reject", json={"reason": "Not relevant"}, headers=auth_headers)
        assert r.status_code == 200

    def test_cannot_approve_twice(self, client, auth_headers, db, test_user):
        user_id = test_user["user"]["id"]
        a_id, d_id = self._setup_approval(client, auth_headers, db, user_id)
        # First approve
        client.post(f"/api/approvals/{a_id}/approve", json={}, headers=auth_headers)
        # Second approve should fail
        r = client.post(f"/api/approvals/{a_id}/approve", json={}, headers=auth_headers)
        assert r.status_code == 400

    def test_send_blocked_without_approval(self, client, auth_headers, db, test_user):
        """Backend must block email send without prior approval."""
        user_id = test_user["user"]["id"]
        a_id, d_id = self._setup_approval(client, auth_headers, db, user_id)
        # Try to send WITHOUT approving first
        r = client.post(f"/api/approvals/{a_id}/send", headers=auth_headers)
        assert r.status_code == 403


# ── Agent Status Tests ─────────────────────────────────────────────────────────

class TestAgents:
    def test_list_agents(self, client, auth_headers):
        r = client.get("/api/agents", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data["agents"]) == 6
        assert "llm_status" in data

    def test_agent_system_status(self, client, auth_headers):
        r = client.get("/api/agents/status", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["system"] == "operational"
        assert "demo_mode" in data


# ── LLM / Research Demo Mode Tests ────────────────────────────────────────────

class TestDemoMode:
    def test_demo_mode_flag_in_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        # In testing, demo_mode should be true
        data = r.json()
        assert "demo_mode" in data

    def test_research_agent_demo(self):
        """Research agent returns mock data in demo mode."""
        import asyncio
        from backend.app.agents.research_agent import research_agent
        result = asyncio.run(research_agent.research("Test instruction for demo mode", target_count=3))
        assert result.is_demo is True
        assert len(result.prospects) > 0
        # All demo prospects should be labeled
        for p in result.prospects:
            assert p.is_demo is True

    def test_analysis_agent_demo(self):
        """Analysis agent scores prospects in demo mode."""
        import asyncio
        from backend.app.agents.research_agent import ProspectResearch
        from backend.app.agents.analysis_agent import analysis_agent

        prospects = [ProspectResearch(
            company_name="Test Company",
            industry="Technology",
            description="A test company",
            location="Bengaluru",
            research_confidence=0.8,
        )]
        result = asyncio.run(analysis_agent.analyze(prospects, "{}", "Find tech companies"))
        assert len(result.scored_prospects) == 1
        score = result.scored_prospects[0]
        assert 0 <= score.lead_score <= 100
        assert score.priority in ("HIGH", "MEDIUM", "LOW")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
