"""Database initialization and seed script."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.database import init_db, engine, Base
from backend.app.config import get_settings

settings = get_settings()


def main():
    print("BizPilot AI – Database Initialization")
    print(f"Database: {settings.database_url[:40]}…")
    print("Creating tables…")
    
    # Import all models so they register with Base
    from backend.app.models import (
        User, BusinessProfile, Workflow, Prospect,
        LeadAnalysis, MarketingDraft, Approval, Report, ExecutionLog
    )
    
    init_db()
    print("✅ All tables created successfully.")
    print("\nNext steps:")
    print("  1. Run: python scripts/seed_demo_data.py")
    print("  2. Start backend: uvicorn backend.app.main:app --reload")
    print("  3. Start frontend: streamlit run frontend/app.py")


if __name__ == "__main__":
    main()
