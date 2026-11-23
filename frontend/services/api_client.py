"""BizPilot AI – Streamlit Frontend API service layer."""
import requests
import os
from typing import Optional, Dict, Any

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


class APIClient:
    def __init__(self, token: Optional[str] = None):
        self.base = BACKEND_URL
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def _get(self, path: str, params: dict = None) -> Optional[Any]:
        try:
            r = requests.get(f"{self.base}{path}", headers=self.headers, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.ConnectionError:
            return None
        except Exception as e:
            return None

    def _post(self, path: str, data: dict = None) -> Optional[Any]:
        try:
            r = requests.post(f"{self.base}{path}", json=data, headers=self.headers, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return None

    def _put(self, path: str, data: dict = None) -> Optional[Any]:
        try:
            r = requests.put(f"{self.base}{path}", json=data, headers=self.headers, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    def _delete(self, path: str) -> bool:
        try:
            r = requests.delete(f"{self.base}{path}", headers=self.headers, timeout=10)
            return r.status_code == 200
        except Exception:
            return False

    def health(self) -> dict:
        return self._get("/health") or {"status": "unreachable"}

    # Auth
    def login(self, email: str, password: str) -> Optional[dict]:
        return self._post("/api/auth/login", {"email": email, "password": password})

    def register(self, email: str, password: str, full_name: str = "") -> Optional[dict]:
        return self._post("/api/auth/register", {"email": email, "password": password, "full_name": full_name})

    def me(self) -> Optional[dict]:
        return self._get("/api/auth/me")

    # Workflows
    def create_workflow(self, instruction: str, title: str = None, target_count: int = 5, min_lead_score: int = 40) -> Optional[dict]:
        return self._post("/api/workflows", {"instruction": instruction, "title": title, "target_count": target_count, "min_lead_score": min_lead_score})

    def list_workflows(self) -> list:
        return self._get("/api/workflows") or []

    def get_workflow(self, wf_id: str) -> Optional[dict]:
        return self._get(f"/api/workflows/{wf_id}")

    def resume_workflow(self, wf_id: str) -> Optional[dict]:
        return self._post(f"/api/workflows/{wf_id}/resume")

    def cancel_workflow(self, wf_id: str) -> Optional[dict]:
        return self._post(f"/api/workflows/{wf_id}/cancel")

    # Prospects
    def list_prospects(self, search: str = None, priority: str = None, page: int = 1) -> list:
        params = {"page": page}
        if search:
            params["search"] = search
        if priority:
            params["priority"] = priority
        return self._get("/api/prospects", params=params) or []

    def create_prospect(self, data: dict) -> Optional[dict]:
        return self._post("/api/prospects", data)

    def update_prospect(self, pid: str, data: dict) -> Optional[dict]:
        return self._put(f"/api/prospects/{pid}", data)

    def delete_prospect(self, pid: str) -> bool:
        return self._delete(f"/api/prospects/{pid}")

    # Approvals
    def list_approvals(self, status: str = None) -> list:
        params = {}
        if status:
            params["status"] = status
        return self._get("/api/approvals", params=params) or []

    def approve_action(self, approval_id: str, edited_subject: str = None, edited_body: str = None) -> Optional[dict]:
        data = {}
        if edited_subject:
            data["edited_subject"] = edited_subject
        if edited_body:
            data["edited_body"] = edited_body
        return self._post(f"/api/approvals/{approval_id}/approve", data)

    def reject_action(self, approval_id: str, reason: str = "") -> Optional[dict]:
        return self._post(f"/api/approvals/{approval_id}/reject", {"reason": reason})

    def send_email(self, approval_id: str) -> Optional[dict]:
        return self._post(f"/api/approvals/{approval_id}/send")

    # Marketing
    def list_drafts(self) -> list:
        return self._get("/api/marketing/drafts") or []

    def get_draft(self, draft_id: str) -> Optional[dict]:
        return self._get(f"/api/marketing/drafts/{draft_id}")

    def update_draft(self, draft_id: str, subject: str = None, body: str = None) -> Optional[dict]:
        data = {}
        if subject:
            data["subject"] = subject
        if body:
            data["body"] = body
        return self._put(f"/api/marketing/drafts/{draft_id}", data)

    # Reports
    def list_reports(self) -> list:
        return self._get("/api/reports") or []

    def get_report(self, report_id: str) -> Optional[dict]:
        return self._get(f"/api/reports/{report_id}")

    def export_csv(self, report_id: str) -> Optional[bytes]:
        try:
            r = requests.get(f"{self.base}/api/reports/{report_id}/export/csv", headers=self.headers, timeout=30)
            r.raise_for_status()
            return r.content
        except Exception:
            return None

    # Business profile
    def get_profile(self) -> Optional[dict]:
        return self._get("/api/business/profile")

    def create_profile(self, data: dict) -> Optional[dict]:
        return self._post("/api/business/profile", data)

    def update_profile(self, data: dict) -> Optional[dict]:
        return self._put("/api/business/profile", data)

    # Agents
    def agent_status(self) -> Optional[dict]:
        return self._get("/api/agents/status")
