"""BizPilot AI – Main Streamlit Dashboard Application."""
import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BizPilot AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Global */
[data-testid="stAppViewContainer"] { background: #0f0f1a; }
[data-testid="stSidebar"] { background: #12122a !important; border-right: 1px solid #2d2d44; }
h1,h2,h3,h4,h5,h6 { color: #e2e8f0 !important; }
p, li, div { color: #cbd5e1; }
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div { background: #1e1e2e !important; border: 1px solid #3d3d5c !important; color: #e2e8f0 !important; border-radius: 8px !important; }
.stButton > button { background: linear-gradient(135deg,#6366f1,#8b5cf6) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; padding: 0.5rem 1.5rem !important; }
.stButton > button:hover { opacity: 0.9 !important; transform: translateY(-1px); }
[data-testid="stMetricValue"] { color: #e2e8f0 !important; font-weight: 700; }
[data-testid="stMetricLabel"] { color: #8b8ba7 !important; }
.stDataFrame { border: 1px solid #2d2d44; border-radius: 8px; }
div[data-testid="stExpander"] { background: #1e1e2e; border: 1px solid #2d2d44; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ── Session state init ─────────────────────────────────────────────────────────
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

from services.api_client import APIClient


def get_client() -> APIClient:
    return APIClient(token=st.session_state.get("token"))


# ── Auth ───────────────────────────────────────────────────────────────────────
def show_auth():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;padding:2rem 0 1rem;">
            <h1 style="font-size:2.5rem;background:linear-gradient(135deg,#6366f1,#8b5cf6);
                       -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;">
                🚀 BizPilot AI
            </h1>
            <p style="color:#8b8ba7;margin:0.5rem 0 2rem;">
                One Instruction. Complete Business Execution.
            </p>
        </div>
        """, unsafe_allow_html=True)

        health = get_client().health()
        if health.get("status") == "unreachable":
            st.error("⚠️ Backend not reachable. Start the API server first: `uvicorn backend.app.main:app --reload`")
            return

        tab1, tab2 = st.tabs(["Sign In", "Create Account"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@company.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In", use_container_width=True)
                if submitted:
                    result = get_client().login(email, password)
                    if result and "access_token" in result:
                        st.session_state.token = result["access_token"]
                        st.session_state.user = result["user"]
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

        with tab2:
            with st.form("register_form"):
                full_name = st.text_input("Full Name")
                email = st.text_input("Email", placeholder="you@company.com")
                password = st.text_input("Password", type="password", help="Minimum 8 characters")
                submitted = st.form_submit_button("Create Account", use_container_width=True)
                if submitted:
                    result = get_client().register(email, password, full_name)
                    if result and "access_token" in result:
                        st.session_state.token = result["access_token"]
                        st.session_state.user = result["user"]
                        st.rerun()
                    else:
                        st.error("Registration failed. Email may already be registered.")


# ── Sidebar ────────────────────────────────────────────────────────────────────
def show_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:1rem 0 1.5rem;">
            <h2 style="margin:0;font-size:1.4rem;background:linear-gradient(135deg,#6366f1,#8b5cf6);
                       -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                🚀 BizPilot AI
            </h2>
            <p style="color:#8b8ba7;margin:0.2rem 0 0;font-size:0.78rem;">Business Automation Platform</p>
        </div>
        """, unsafe_allow_html=True)

        user = st.session_state.get("user", {})
        st.markdown(f"""
        <div style="background:#1e1e2e;border-radius:8px;padding:0.7rem 1rem;margin-bottom:1.5rem;
                    border:1px solid #2d2d44;">
            <p style="margin:0;font-size:0.82rem;color:#8b8ba7;">Signed in as</p>
            <p style="margin:0;font-weight:600;color:#e2e8f0;font-size:0.9rem;">
                {user.get('full_name', 'User') or user.get('email','')[:20]}
            </p>
        </div>
        """, unsafe_allow_html=True)

        pages = {
            "Dashboard": "📊",
            "AI Assistant": "🤖",
            "Agent Monitor": "⚙️",
            "Prospects": "🔍",
            "CRM": "👥",
            "Marketing Studio": "✉️",
            "Approval Center": "✅",
            "Reports": "📈",
            "Settings": "⚙️",
        }

        if "page" not in st.session_state:
            st.session_state.page = "Dashboard"

        for page, icon in pages.items():
            is_active = st.session_state.page == page
            if st.sidebar.button(
                f"{icon}  {page}",
                key=f"nav_{page}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.page = page
                st.rerun()

        st.sidebar.markdown("---")
        # Pending approvals badge
        client = get_client()
        approvals = client.list_approvals(status="PENDING")
        if approvals:
            st.sidebar.warning(f"🔔 {len(approvals)} pending approval(s)")

        if st.sidebar.button("Sign Out", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()


# ── Pages ──────────────────────────────────────────────────────────────────────
def page_dashboard():
    client = get_client()
    st.markdown("## 📊 Dashboard")

    workflows = client.list_workflows()
    prospects = client.list_prospects()
    approvals_pending = client.list_approvals(status="PENDING")
    reports = client.list_reports()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Prospects", len(prospects))
    with c2:
        high = sum(1 for p in prospects if p.get("priority") == "HIGH")
        st.metric("High-Priority Leads", high)
    with c3:
        active = sum(1 for w in workflows if w.get("status") in ("RUNNING", "PENDING", "PAUSED"))
        st.metric("Active Workflows", active)
    with c4:
        st.metric("Pending Approvals", len(approvals_pending))

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Recent Workflows")
        if workflows:
            for w in workflows[:5]:
                status = w.get("status", "")
                color = {"COMPLETED": "🟢", "RUNNING": "🔵", "PAUSED": "🟡", "FAILED": "🔴"}.get(status, "⚪")
                st.markdown(f"{color} **{w.get('title','')[:50]}** — `{status}`")
                st.caption(f"Step: {w.get('current_step','—')}  |  Created: {str(w.get('created_at',''))[:16]}")
        else:
            st.info("No workflows yet. Use the AI Assistant to start one.")

    with col2:
        if prospects:
            import plotly.express as px
            import pandas as pd

            priorities = [p.get("priority") or "UNKNOWN" for p in prospects]
            df = pd.DataFrame({"Priority": priorities})
            fig = px.pie(
                df,
                names="Priority",
                title="Lead Priority Distribution",
                color="Priority",
                color_discrete_map={"HIGH": "#dc3545", "MEDIUM": "#fd7e14", "LOW": "#198754", "UNKNOWN": "#6c757d"},
                hole=0.4,
            )
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No prospect data yet.")


def page_ai_assistant():
    client = get_client()
    st.markdown("## 🤖 AI Business Assistant")
    st.markdown("Enter a natural-language instruction. BizPilot AI will research, analyze, generate drafts, and ask for your approval before any action.")

    # Health check
    health = client.health()
    demo = health.get("demo_mode", True)
    if demo:
        st.info("🔬 **Demo Mode** – Running with mock data. Set `GROQ_API_KEY` in `.env` for real AI.")

    with st.form("workflow_form"):
        st.markdown("**Your Business Instruction**")
        instruction = st.text_area(
            "instruction",
            height=120,
            placeholder="e.g. Find 10 healthcare startups in Bengaluru that need AI automation. Research them, score leads, generate marketing emails, save to CRM.",
            label_visibility="collapsed",
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            target_count = st.number_input("Max Prospects", min_value=1, max_value=20, value=5)
        with col2:
            min_score = st.number_input("Min Lead Score", min_value=0, max_value=100, value=40)
        with col3:
            title = st.text_input("Workflow Title (optional)", placeholder="My Campaign")

        submitted = st.form_submit_button("🚀 Start Workflow", use_container_width=True)

        if submitted:
            if not instruction.strip() or len(instruction.strip()) < 10:
                st.error("Please enter a detailed instruction (at least 10 characters).")
            else:
                with st.spinner("Creating workflow and launching agents…"):
                    result = client.create_workflow(instruction.strip(), title or None, target_count, min_score)
                if result and "id" in result:
                    st.success(f"✅ Workflow started! ID: `{result['id'][:8]}…`")
                    st.info("Agents are running in the background. Refresh to see status updates.")
                    st.session_state["last_workflow_id"] = result["id"]
                else:
                    st.error("Failed to start workflow. Is the backend running?")

    # Show workflow status if one was just started
    last_id = st.session_state.get("last_workflow_id")
    if last_id:
        st.markdown("---")
        st.markdown("### Workflow Status")
        wf = client.get_workflow(last_id)
        if wf:
            status = wf.get("status", "")
            st.markdown(f"**Status:** `{status}` | **Step:** `{wf.get('current_step','—')}`")
            if status == "PAUSED":
                st.warning("⏸ Workflow paused – awaiting approval. Visit the **Approval Center** to review and approve actions.")
                if st.button("Go to Approval Center"):
                    st.session_state.page = "Approval Center"
                    st.rerun()
            elif status == "COMPLETED":
                st.success("✅ Workflow completed! Check Reports for the final summary.")
            elif status == "FAILED":
                st.error(f"Workflow failed: {wf.get('error_message', 'Unknown error')}")
            if st.button("🔄 Refresh Status"):
                st.rerun()


def page_agent_monitor():
    client = get_client()
    st.markdown("## ⚙️ Agent Monitor")

    status = client.agent_status() or {}
    agents_data = client.get_client().agent_status() if hasattr(client, "get_client") else status

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Agents", status.get("agent_count", 6))
    with col2:
        st.metric("LLM Configured", "Yes" if status.get("llm_configured") else "No (Demo)")
    with col3:
        st.metric("Demo Mode", "Active" if status.get("demo_mode") else "Inactive")

    st.markdown("---")
    agents = [
        {"name": "Research Agent", "purpose": "Finds and researches business prospects", "icon": "🔍", "id": "research"},
        {"name": "Analysis Agent", "purpose": "Scores and ranks prospects by business potential", "icon": "📊", "id": "analysis"},
        {"name": "Marketing Agent", "purpose": "Generates personalized email drafts", "icon": "✉️", "id": "marketing"},
        {"name": "CRM Agent", "purpose": "Saves prospects and drafts to database", "icon": "👥", "id": "crm"},
        {"name": "Approval Agent", "purpose": "Human-in-the-loop approval management", "icon": "✅", "id": "approval"},
        {"name": "Reporting Agent", "purpose": "Generates business intelligence reports", "icon": "📈", "id": "reporting"},
    ]

    for i in range(0, 6, 2):
        c1, c2 = st.columns(2)
        for col, agent in zip([c1, c2], agents[i:i+2]):
            with col:
                st.markdown(f"""
                <div style="background:#1e1e2e;border:1px solid #2d2d44;border-radius:12px;padding:1.2rem;">
                    <h4 style="margin:0;">{agent['icon']} {agent['name']}</h4>
                    <p style="color:#8b8ba7;font-size:0.85rem;margin:0.5rem 0;">{agent['purpose']}</p>
                    <span style="background:#198754;color:white;padding:2px 10px;border-radius:12px;font-size:0.75rem;">READY</span>
                </div>
                """, unsafe_allow_html=True)


def page_prospects():
    client = get_client()
    st.markdown("## 🔍 Prospect Research")

    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        search = st.text_input("Search companies", placeholder="e.g. TechFlow")
    with col2:
        priority_filter = st.selectbox("Priority", ["All", "HIGH", "MEDIUM", "LOW"])
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh"):
            st.rerun()

    priority = None if priority_filter == "All" else priority_filter
    prospects = client.list_prospects(search=search or None, priority=priority)

    if not prospects:
        st.info("No prospects found. Run a workflow to research prospects.")
        return

    import pandas as pd
    rows = []
    for p in prospects:
        rows.append({
            "Company": p.get("company_name", ""),
            "Industry": p.get("industry", ""),
            "Location": p.get("location", ""),
            "Score": p.get("lead_score") or "—",
            "Priority": p.get("priority") or "—",
            "Status": p.get("research_status", ""),
            "Demo": "🔬" if p.get("is_demo") else "✅",
            "Contact": p.get("contact_email") or "unknown",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(prospects)} prospect(s)")


def page_crm():
    client = get_client()
    st.markdown("## 👥 CRM")

    tab1, tab2 = st.tabs(["All Prospects", "Add Prospect"])

    with tab1:
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("Search", placeholder="Company name")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            priority_f = st.selectbox("Priority", ["All", "HIGH", "MEDIUM", "LOW"], key="crm_pf")

        priority = None if priority_f == "All" else priority_f
        prospects = client.list_prospects(search=search or None, priority=priority)

        if not prospects:
            st.info("No CRM records yet.")
            return

        for p in prospects:
            with st.expander(f"{p.get('company_name','')} — Score: {p.get('lead_score','—')} | {p.get('priority','—')}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Industry:** {p.get('industry','—')}")
                    st.write(f"**Location:** {p.get('location','—')}")
                    st.write(f"**Website:** {p.get('website','—')}")
                with c2:
                    st.write(f"**Contact:** {p.get('contact_email','—')}")
                    st.write(f"**Research:** {p.get('research_status','—')}")
                    st.write(f"**Demo Data:** {'Yes' if p.get('is_demo') else 'No'}")
                st.write(f"**Description:** {p.get('description','—')}")
                if st.button(f"Delete", key=f"del_{p['id']}"):
                    if client.delete_prospect(p["id"]):
                        st.success("Deleted")
                        st.rerun()

    with tab2:
        with st.form("add_prospect_form"):
            company_name = st.text_input("Company Name *")
            website = st.text_input("Website")
            industry = st.text_input("Industry")
            location = st.text_input("Location")
            contact_email = st.text_input("Contact Email")
            description = st.text_area("Description")
            if st.form_submit_button("Add Prospect", use_container_width=True):
                data = {"company_name": company_name, "website": website, "industry": industry,
                        "location": location, "contact_email": contact_email, "description": description}
                result = client.create_prospect(data)
                if result:
                    st.success(f"Added {company_name}")
                    st.rerun()
                else:
                    st.error("Failed to add prospect (may already exist)")


def page_marketing():
    client = get_client()
    st.markdown("## ✉️ Marketing Studio")

    drafts = client.list_drafts()
    if not drafts:
        st.info("No email drafts yet. Run a workflow to generate personalized email drafts.")
        return

    st.markdown(f"**{len(drafts)} draft(s) generated**")
    for d in drafts:
        status = d.get("status", "DRAFT")
        color = {"DRAFT": "🟡", "APPROVED": "🟢", "REJECTED": "🔴", "SENT": "🔵"}.get(status, "⚪")
        with st.expander(f"{color} {d.get('subject','')[:60]}… | {status}"):
            st.markdown(f"**Recipient:** {d.get('recipient_email','unknown')}")
            st.markdown(f"**Marketing Angle:** {d.get('marketing_angle','—')}")
            full = client.get_draft(d["id"])
            if full:
                st.text_area("Email Body", value=full.get("body", ""), height=200, key=f"body_{d['id']}", disabled=True)
                if full.get("personalization_notes"):
                    st.caption(f"Personalization: {full['personalization_notes']}")


def page_approvals():
    client = get_client()
    st.markdown("## ✅ Approval Center")
    st.markdown("Review and approve actions before they execute. **No email is sent without your explicit approval.**")

    tab1, tab2 = st.tabs(["Pending", "History"])

    with tab1:
        pending = client.list_approvals(status="PENDING")
        if not pending:
            st.success("✅ No pending approvals. All actions reviewed.")
        else:
            st.warning(f"⚠️ {len(pending)} action(s) waiting for your review")
            for a in pending:
                with st.expander(f"📧 {a.get('action_description','')[:60]} — PENDING"):
                    st.markdown(f"**Action Type:** `{a.get('action_type','')}`")
                    st.markdown(f"**Target Email:** {a.get('target_email') or 'not specified'}")
                    if a.get("draft_subject"):
                        st.markdown(f"**Subject:** {a['draft_subject']}")
                    if a.get("draft_body"):
                        st.text_area("Email Preview", value=a["draft_body"], height=200, key=f"preview_{a['id']}", disabled=True)

                    edited_subject = st.text_input("Edit Subject (optional)", key=f"es_{a['id']}")
                    edited_body = st.text_area("Edit Body (optional)", height=100, key=f"eb_{a['id']}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Approve", key=f"approve_{a['id']}", use_container_width=True):
                            result = client.approve_action(a["id"], edited_subject or None, edited_body or None)
                            if result:
                                st.success("Approved!")
                                st.rerun()
                    with col2:
                        reason = st.text_input("Rejection reason", key=f"reason_{a['id']}")
                        if st.button("❌ Reject", key=f"reject_{a['id']}", use_container_width=True):
                            result = client.reject_action(a["id"], reason)
                            if result:
                                st.info("Rejected.")
                                st.rerun()

    with tab2:
        all_approvals = client.list_approvals()
        history = [a for a in all_approvals if a.get("status") != "PENDING"]
        if not history:
            st.info("No approval history yet.")
        else:
            import pandas as pd
            rows = [{"Status": a.get("status"), "Type": a.get("action_type"), 
                     "Target": a.get("target_email","—"), "Reviewed By": a.get("approved_by","—"),
                     "Date": str(a.get("approved_at","—"))[:16]} for a in history]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def page_reports():
    client = get_client()
    st.markdown("## 📈 Reports & Analytics")

    reports = client.list_reports()
    if not reports:
        st.info("No reports yet. Complete a workflow to generate a report.")
        return

    for r in reports:
        with st.expander(f"📋 {r.get('title','')} — {str(r.get('created_at',''))[:16]}"):
            st.markdown(f"**Summary:** {r.get('summary','')}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Prospects", r.get("total_prospects", 0))
            c2.metric("High Priority", r.get("high_priority", 0))
            c3.metric("Medium Priority", r.get("medium_priority", 0))
            c4.metric("Drafts Generated", r.get("drafts_generated", 0))

            full = client.get_report(r["id"])
            if full:
                recs = full.get("recommendations", [])
                if recs:
                    st.markdown("**Recommendations:**")
                    for rec in recs:
                        st.markdown(f"• {rec}")
                top = full.get("top_prospects", [])
                if top:
                    import pandas as pd
                    st.markdown("**Top Prospects:**")
                    st.dataframe(pd.DataFrame(top), use_container_width=True, hide_index=True)

            csv_data = client.export_csv(r["id"])
            if csv_data:
                st.download_button(
                    "📥 Download CSV",
                    data=csv_data,
                    file_name=f"bizpilot_report_{r['id'][:8]}.csv",
                    mime="text/csv",
                )


def page_settings():
    client = get_client()
    st.markdown("## ⚙️ Settings")

    tab1, tab2 = st.tabs(["Business Profile", "System Status"])

    with tab1:
        profile = client.get_profile()
        with st.form("profile_form"):
            biz_name = st.text_input("Business Name *", value=profile.get("business_name","") if profile else "")
            description = st.text_area("Business Description *", value=profile.get("description","") if profile else "", height=100)
            services = st.text_area("Products & Services *", value=profile.get("services","") if profile else "", height=80, placeholder="e.g. AI automation consulting, process optimization")
            industries = st.text_input("Target Industries", value=profile.get("target_industries","") if profile else "")
            locations = st.text_input("Target Locations", value=profile.get("target_locations","") if profile else "")
            ideal_customer = st.text_area("Ideal Customer Profile", value=profile.get("ideal_customer","") if profile else "", height=70)
            tone = st.selectbox("Communication Tone", ["professional", "friendly", "formal", "casual"],
                               index=["professional","friendly","formal","casual"].index(profile.get("tone","professional")) if profile else 0)
            website = st.text_input("Company Website", value=profile.get("website","") if profile else "")
            biz_email = st.text_input("Business Email", value=profile.get("business_email","") if profile else "")

            if st.form_submit_button("Save Profile", use_container_width=True):
                data = {"business_name": biz_name, "description": description, "services": services,
                        "target_industries": industries, "target_locations": locations,
                        "ideal_customer": ideal_customer, "tone": tone, "website": website,
                        "business_email": biz_email}
                if profile:
                    result = client.update_profile(data)
                else:
                    result = client.create_profile(data)
                if result:
                    st.success("Profile saved!")
                else:
                    st.error("Failed to save profile")

    with tab2:
        health = client.health()
        status = client.agent_status() or {}
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**API Backend**")
            st.markdown(f"Status: {'🟢 Connected' if health.get('status') != 'unreachable' else '🔴 Unreachable'}")
            st.markdown(f"Database: {'🟢' if health.get('database') == 'connected' else '🔴'} {health.get('database','—')}")
            st.markdown(f"Demo Mode: {'⚠️ Active' if health.get('demo_mode') else '✅ Disabled'}")
        with c2:
            st.markdown("**AI Configuration**")
            st.markdown(f"LLM: {'🟢 Groq Configured' if status.get('llm_configured') else '🔬 Demo Mode (no key)'}")
            st.markdown(f"Research: 🔍 {status.get('research_provider','mock')}")
            st.markdown(f"Email: {'📧 Configured' if status.get('email_configured') else '⚠️ Not configured'}")

        st.info("**Note:** API keys are managed via environment variables in `.env`. Never enter keys in this UI.")


# ── Main Router ────────────────────────────────────────────────────────────────
def main():
    if not st.session_state.token:
        show_auth()
        return

    show_sidebar()
    page = st.session_state.get("page", "Dashboard")

    if page == "Dashboard":
        page_dashboard()
    elif page == "AI Assistant":
        page_ai_assistant()
    elif page == "Agent Monitor":
        page_agent_monitor()
    elif page == "Prospects":
        page_prospects()
    elif page == "CRM":
        page_crm()
    elif page == "Marketing Studio":
        page_marketing()
    elif page == "Approval Center":
        page_approvals()
    elif page == "Reports":
        page_reports()
    elif page == "Settings":
        page_settings()


if __name__ == "__main__":
    main()
