"""
Centralized Premium Styling Module
AI-Powered Civic Issue Reporting and Management System

Provides a consistent, minimal, elegant light-themed design system for the
entire civic technology platform.

Design palette:
- Primary background: Warm ivory #F7F6F2 / Pure white #FFFFFF
- Primary accent: Forest green #34483D
- Text: Charcoal #343A36 / Secondary #747A74
- Supporting: Muted sand #B7A98F / Light sage #E8F1E9 / Soft beige #F6F0E3
              Soft terracotta #F8EDE7 / Muted blue #E9EFF4

Typography: Inter (headings and body)
"""

import streamlit as st
from typing import Optional

# ---------------------------------------------------------
# Design Tokens
# ---------------------------------------------------------

COLORS = {
    # Backgrounds
    "bg_primary": "#F7F6F2",      # Warm ivory - main page background
    "bg_surface": "#FFFFFF",      # Pure white - cards, containers
    "bg_sidebar": "#FFFFFF",
    # Accents
    "accent_primary": "#34483D",  # Forest green - primary actions, headings
    "accent_hover": "#2B3A32",
    # Text
    "text_primary": "#343A36",    # Charcoal - headings, primary text
    "text_secondary": "#747A74",  # Muted charcoal - secondary text, labels
    "text_inverse": "#FFFFFF",
    # Supporting surfaces
    "surface_sage": "#E8F1E9",    # Light sage - subtle backgrounds
    "surface_beige": "#F6F0E3",   # Soft beige - subtle backgrounds
    "surface_terracotta": "#F8EDE7",  # Soft terracotta - alerts
    "surface_blue": "#E9EFF4",    # Muted blue - info backgrounds
    # Borders
    "border_light": "#D8D6CF",
    "border_focus": "#34483D",
    # Status colors
    "status_submitted": "#B7A98F",
    "status_under_review": "#34483D",
    "status_approved": "#B7A98F",
    "status_in_progress": "#B7A98F",
    "status_resolved": "#34483D",
    "status_rejected": "#B7A98F",
}

# ---------------------------------------------------------
# CSS Injection
# ---------------------------------------------------------

PREMIUM_CSS = """
<style>
/* Import Inter typography */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Global base styles */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #F7F6F2 !important;
    color: #343A36 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

[data-testid="stAppViewContainer"] > .main {
    background-color: #F7F6F2 !important;
    padding: 0 !important;
}

[data-testid="stHeader"] {
    background-color: #F7F6F2 !important;
}

/* Hide default Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stDecoration"] {display: none;}

/* Main content area */
.block-container {
    background-color: #F7F6F2 !important;
    padding: 2rem 3rem !important;
    max-width: 1200px !important;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', sans-serif !important;
    color: #343A36 !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
}

h1 {
    font-size: 2rem !important;
    margin-bottom: 0.5rem !important;
}

h2 {
    font-size: 1.5rem !important;
    margin-top: 2rem !important;
    margin-bottom: 1rem !important;
}

h3 {
    font-size: 1.25rem !important;
    margin-top: 1.5rem !important;
    margin-bottom: 0.75rem !important;
}

p, span, div, label {
    color: #343A36;
}

/* Ensure text inside custom containers is visible */
.complaint-card, .kpi-card, .form-section, .empty-state, .page-header {
    color: #343A36;
}

/* Placeholder text visibility */
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: #9CA3AF !important;
    opacity: 1 !important;
}

/* Selectbox and dropdown text visibility */
.stSelectbox > div > div > div > div {
    color: #343A36 !important;
}
.stSelectbox > div > div > div {
    color: #343A36 !important;
}

/* Radio button text visibility */
[data-testid="stRadio"] label {
    color: #343A36 !important;
}

/* Tab text visibility */
[data-testid="stTabs"] [data-testid="stTab"] {
    color: #343A36 !important;
}

/* File uploader text visibility */
.stFileUploader {
    color: #343A36 !important;
}

/* Caption and helper text */
.caption, .stCaption {
    color: #747A74 !important;
}

/* Button text - ensure contrast */
.stButton > button[kind="primary"] {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}
.stButton > button[kind="secondary"] {
    color: #343A36 !important;
    font-weight: 600 !important;
}

/* Info/warning/error message text */
.stAlert > div {
    color: #343A36 !important;
}

.secondary-text {
    color: #747A74 !important;
    font-size: 0.875rem !important;
}

/* Sidebar - minimal and clean */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #D8D6CF !important;
    padding: 1.5rem 1rem !important;
    width: 260px !important;
}

[data-testid="stSidebar"] .block-container {
    padding: 0 !important;
    max-width: none !important;
}

.sidebar-brand {
    font-family: 'Inter', sans-serif !important;
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    color: #34483D !important;
    margin-bottom: 2rem !important;
    letter-spacing: -0.02em !important;
}

.sidebar-user-name {
    font-weight: 600 !important;
    color: #343A36 !important;
    font-size: 0.95rem !important;
    margin-bottom: 0.25rem !important;
}

.sidebar-user-email {
    color: #747A74 !important;
    font-size: 0.8rem !important;
    margin-bottom: 1.5rem !important;
}

.sidebar-divider {
    border: none !important;
    border-top: 1px solid #D8D6CF !important;
    margin: 1rem 0 !important;
}

.sidebar-section-label {
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    color: #747A74 !important;
    font-weight: 600 !important;
    margin-bottom: 0.75rem !important;
}

/* Custom radio navigation */
[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    background-color: transparent !important;
    border: none !important;
    padding: 0 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    display: flex !important;
    align-items: center !important;
    padding: 0.625rem 1rem !important;
    margin-bottom: 0.375rem !important;
    border-radius: 8px !important;
    color: #747A74 !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    border: 1px solid transparent !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background-color: #F6F0E3 !important;
    color: #343A36 !important;
    border-color: #D8D6CF !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] [data-checked="true"],
[data-testid="stSidebar"] [data-baseweb="radio"] [aria-checked="true"] {
    background-color: #34483D !important;
    color: #FFFFFF !important;
    border-color: #34483D !important;
}

/* Hide the default radio circle */
[data-testid="stSidebar"] [data-testid="stRadio"] div[data-testid="stRadio"] > div {
    display: none !important;
}

/* Logout button */
[data-testid="stSidebar"] button[kind="secondary"] {
    background-color: #F8EDE7 !important;
    color: #34483D !important;
    border: 1px solid #D8D6CF !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.625rem 1rem !important;
    border-radius: 8px !important;
    width: 100% !important;
    margin-top: 1rem !important;
}

[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background-color: #F7F6F2 !important;
    border-color: #B7A98F !important;
}

/* Page header */
.page-header {
    margin-bottom: 2.5rem !important;
}

.page-title {
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    color: #343A36 !important;
    margin: 0 0 0.5rem 0 !important;
    letter-spacing: -0.02em !important;
}

.page-subtitle {
    font-size: 0.95rem !important;
    color: #747A74 !important;
    margin: 0 !important;
}

/* KPI Cards */
.kpi-grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)) !important;
    gap: 1rem !important;
    margin-bottom: 2rem !important;
}

.kpi-card {
    background-color: #FFFFFF !important;
    border: 1px solid #D8D6CF !important;
    border-radius: 10px !important;
    padding: 1.25rem !important;
    display: flex !important;
    flex-direction: column !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
}

.kpi-card .kpi-label {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    color: #747A74 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    margin-bottom: 0.5rem !important;
}

.kpi-card .kpi-value {
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    color: #343A36 !important;
    margin: 0 !important;
    line-height: 1.2 !important;
}

/* Status Badge */
.status-badge {
    display: inline-flex !important;
    align-items: center !important;
    padding: 0.375rem 0.875rem !important;
    border-radius: 9999px !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.03em !important;
    border: 1px solid !important;
}

/* Status variants */
.status-submitted-badge {
    background-color: #E9EFF4 !important;
    color: #34483D !important;
    border-color: #D8D6CF !important;
}
.status-under-review-badge {
    background-color: #E8F1E9 !important;
    color: #34483D !important;
    border-color: #B7A98F !important;
}
.status-approved-badge {
    background-color: #F6F0E3 !important;
    color: #34483D !important;
    border-color: #D8D6CF !important;
}
.status-in-progress-badge {
    background-color: #F6F0E3 !important;
    color: #34483D !important;
    border-color: #D8D6CF !important;
}
.status-resolved-badge {
    background-color: #E8F1E9 !important;
    color: #34483D !important;
    border-color: #B7A98F !important;
}
.status-rejected-badge {
    background-color: #F8EDE7 !important;
    color: #34483D !important;
    border-color: #D8D6CF !important;
}

/* Complaint Cards */
.complaint-card {
    background-color: #FFFFFF !important;
    border: 1px solid #D8D6CF !important;
    border-radius: 10px !important;
    padding: 1.25rem !important;
    margin-bottom: 1rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
    transition: box-shadow 0.15s ease !important;
}

.complaint-card:hover {
    box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
}

.complaint-card .complaint-header {
    display: flex !important;
    justify-content: space-between !important;
    align-items: flex-start !important;
    margin-bottom: 0.75rem !important;
}

.complaint-card .complaint-title {
    font-size: 1rem !important;
    font-weight: 700 !important;
    color: #343A36 !important;
    margin: 0 !important;
}

.complaint-card .complaint-meta {
    font-size: 0.85rem !important;
    color: #747A74 !important;
    margin-top: 0.375rem !important;
    line-height: 1.5 !important;
}

/* Form Sections */
.form-section {
    background-color: #FFFFFF !important;
    border: 1px solid #D8D6CF !important;
    border-radius: 10px !important;
    padding: 1.5rem !important;
    margin-bottom: 1.5rem !important;
}

.form-section-title {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #343A36 !important;
    margin: 0 0 1rem 0 !important;
    padding-bottom: 0.5rem !important;
    border-bottom: 1px solid #D8D6CF !important;
}

/* Buttons - primary */
.stButton > button[kind="primary"] {
    background-color: #34483D !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.625rem 1.25rem !important;
    transition: background-color 0.15s ease !important;
}

.stButton > button[kind="primary"]:hover {
    background-color: #2B3A32 !important;
}

/* Buttons - secondary */
.stButton > button[kind="secondary"] {
    background-color: #FFFFFF !important;
    color: #343A36 !important;
    border: 1px solid #D8D6CF !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.625rem 1.25rem !important;
    transition: all 0.15s ease !important;
}

.stButton > button[kind="secondary"]:hover {
    background-color: #F7F6F2 !important;
    border-color: #B7A98F !important;
}

/* Input fields */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background-color: #FFFFFF !important;
    border: 1px solid #D8D6CF !important;
    border-radius: 8px !important;
    color: #343A36 !important;
    font-size: 0.9rem !important;
    padding: 0.625rem 0.875rem !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > div:focus {
    border-color: #34483D !important;
    box-shadow: 0 0 0 2px rgba(52, 72, 61, 0.1) !important;
}

/* Labels */
label {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #343A36 !important;
    margin-bottom: 0.375rem !important;
}

/* Empty States */
.empty-state {
    text-align: center !important;
    padding: 3rem 1rem !important;
    color: #747A74 !important;
}

.empty-state-icon {
    font-size: 3rem !important;
    margin-bottom: 1rem !important;
    opacity: 0.4 !important;
}

.empty-state-title {
    font-size: 1.125rem !important;
    font-weight: 600 !important;
    color: #343A36 !important;
    margin-bottom: 0.5rem !important;
}

.empty-state-description {
    font-size: 0.9rem !important;
    color: #747A74 !important;
    margin-bottom: 1.5rem !important;
}

/* Divider */
.section-divider {
    border: none !important;
    border-top: 1px solid #D8D6CF !important;
    margin: 2rem 0 !important;
}

/* Alert / info boxes */
.stAlert {
    border-radius: 8px !important;
    border: 1px solid #D8D6CF !important;
    background-color: #FFFFFF !important;
}

/* Hide emoji from navigation - use clean text only */
[data-testid="stSidebar"] [data-testid="stRadio"] span {
    font-family: 'Inter', sans-serif !important;
}

/* Fix metric styling */
[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border: 1px solid #D8D6CF !important;
    border-radius: 10px !important;
    padding: 1rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
}

[data-testid="stMetric"] label {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    color: #747A74 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    color: #343A36 !important;
}
</style>
"""

def inject_premium_css() -> None:
    """Inject the centralized premium CSS into the Streamlit app."""
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------
# Reusable UI Components
# ---------------------------------------------------------

def page_header(title: str, subtitle: str = "") -> None:
    """Render a clean, minimal page header."""
    st.markdown(f'<div class="page-header"><h1 class="page-title">{title}</h1>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<p class="page-subtitle secondary-text">{subtitle}</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def kpi_card(label: str, value: str) -> None:
    """Render a single KPI card."""
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label secondary-text">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    """Return HTML for a status badge based on the complaint status."""
    badge_map = {
        "Submitted": "status-submitted-badge",
        "Under Review": "status-under-review-badge",
        "Approved": "status-approved-badge",
        "In Progress": "status-in-progress-badge",
        "Resolved": "status-resolved-badge",
        "Rejected": "status-rejected-badge",
    }
    css_class = badge_map.get(status, "status-submitted-badge")
    return f'<span class="status-badge {css_class}">{status}</span>'


def complaint_card(
    complaint_id: int,
    title: str,
    status: str,
    category: str,
    location_address: str,
    created_at: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    image_path: Optional[str] = None,
    show_image: bool = True,
) -> None:
    """Render a clean complaint card."""
    coords_html = ""
    if latitude is not None and longitude is not None:
        coords_html = f'<br/><span style="font-size:0.8rem;color:#747A74;">GPS: ({latitude:.4f}, {longitude:.4f})</span>'

    img_html = ""
    if show_image and image_path:
        from pathlib import Path
        from modules.database import BASE_DIR
        img_file = BASE_DIR / image_path
        if img_file.exists():
            st.markdown('<div class="complaint-card">', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="complaint-header">
                    <h3 class="complaint-title">#{complaint_id} - {title}</h3>
                    {status_badge(status)}
                </div>
                <p class="complaint-meta">
                    <strong>Category:</strong> {category}<br/>
                    <strong>Location:</strong> {location_address}{coords_html}<br/>
                    <strong>Submitted:</strong> {created_at[:16]}
                </p>
                """,
                unsafe_allow_html=True,
            )
            st.image(str(img_file), caption="Complaint Photograph", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            return

    st.markdown('<div class="complaint-card">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="complaint-header">
            <h3 class="complaint-title">#{complaint_id} - {title}</h3>
            {status_badge(status)}
        </div>
        <p class="complaint-meta">
            <strong>Category:</strong> {category}<br/>
            <strong>Location:</strong> {location_address}{coords_html}<br/>
            <strong>Submitted:</strong> {created_at[:16]}
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)


def empty_state(icon: str, title: str, description: str, button_label: str = "", button_key: str = "") -> None:
    """Render a well-designed empty state."""
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="empty-state-icon">{icon}</div>
            <h2 class="empty-state-title">{title}</h2>
            <p class="empty-state-description">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if button_label and button_key:
        if st.button(button_label, key=button_key, type="primary", use_container_width=True):
            st.session_state["_empty_state_action"] = button_key


def form_section(title: str) -> None:
    """Render a form section header."""
    st.markdown(f'<div class="form-section"><h3 class="form-section-title">{title}</h3>', unsafe_allow_html=True)


def close_form_section() -> None:
    """Close a form section div."""
    st.markdown('</div>', unsafe_allow_html=True)


def section_divider() -> None:
    """Render a subtle section divider."""
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


def confirmation_dialog(
    title: str,
    message: str,
    confirm_label: str = "Confirm",
    cancel_label: str = "Cancel",
    key_prefix: str = "confirm",
) -> Optional[bool]:
    """
    Render a confirmation dialog using session state.
    Returns True if confirmed, False if cancelled, None if not yet decided.
    """
    confirmed_key = f"{key_prefix}_confirmed"
    cancelled_key = f"{key_prefix}_cancelled"

    st.markdown(
        f"""
        <div style="background-color:#FFFFFF;border:1px solid #D8D6CF;border-radius:10px;padding:1.5rem;margin:1rem 0;">
            <h3 style="margin-top:0;color:#343A36;font-weight:600;">{title}</h3>
            <p style="color:#747A74;margin-bottom:1.5rem;">{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button(confirm_label, type="primary", use_container_width=True, key=f"{key_prefix}_yes"):
            st.session_state[confirmed_key] = True
            return True
    with col2:
        if st.button(cancel_label, use_container_width=True, key=f"{key_prefix}_no"):
            st.session_state[cancelled_key] = True
            return False

    return None
