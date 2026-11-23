"""Shared Streamlit UI components for BizPilot AI."""
import streamlit as st


def status_badge(status: str) -> str:
    colors = {
        "PENDING": "#6c757d",
        "RUNNING": "#0d6efd",
        "PAUSED": "#fd7e14",
        "AWAITING_APPROVAL": "#fd7e14",
        "COMPLETED": "#198754",
        "FAILED": "#dc3545",
        "CANCELLED": "#6c757d",
        "HIGH": "#dc3545",
        "MEDIUM": "#fd7e14",
        "LOW": "#198754",
        "DRAFT": "#6c757d",
        "APPROVED": "#198754",
        "REJECTED": "#dc3545",
        "SENT": "#0dcaf0",
        "EXECUTED": "#0d6efd",
    }
    color = colors.get(status, "#6c757d")
    return f'<span style="background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:0.78rem;font-weight:600;">{status}</span>'


def metric_card(label: str, value, delta: str = None, icon: str = ""):
    delta_html = f'<p style="color:#198754;margin:0;font-size:0.85rem;">▲ {delta}</p>' if delta else ""
    st.markdown(
        f"""
        <div style="background:#1e1e2e;border:1px solid #2d2d44;border-radius:12px;
                    padding:1.2rem 1.5rem;margin:0.3rem 0;">
            <p style="color:#8b8ba7;margin:0;font-size:0.82rem;font-weight:500;text-transform:uppercase;
                      letter-spacing:0.05em;">{icon} {label}</p>
            <p style="color:#e2e8f0;margin:0.3rem 0 0;font-size:1.9rem;font-weight:700;">{value}</p>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_banner(message: str, kind: str = "info"):
    colors = {"info": "#0d6efd", "success": "#198754", "warning": "#fd7e14", "error": "#dc3545"}
    icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
    color = colors.get(kind, "#0d6efd")
    icon = icons.get(kind, "ℹ️")
    st.markdown(
        f"""
        <div style="border-left:4px solid {color};background:{color}18;border-radius:4px;
                    padding:0.8rem 1rem;margin:0.5rem 0;">
            {icon} {message}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div style="margin-bottom:1.5rem;">
            <h2 style="color:#e2e8f0;margin:0;font-weight:700;">{title}</h2>
            {f'<p style="color:#8b8ba7;margin:0.2rem 0 0;">{subtitle}</p>' if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(icon: str, title: str, description: str):
    st.markdown(
        f"""
        <div style="text-align:center;padding:3rem 1rem;color:#8b8ba7;">
            <div style="font-size:3rem;margin-bottom:1rem;">{icon}</div>
            <h3 style="color:#cbd5e1;margin:0;">{title}</h3>
            <p style="margin:0.5rem 0 0;">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
