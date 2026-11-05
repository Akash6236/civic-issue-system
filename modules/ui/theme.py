"""
Centralized UI Styling Module
AI-Powered Civic Issue Reporting and Management System

Provides a consistent, minimal, elegant light-themed design system for the
entire civic technology platform.

Design palette:
- Primary forest green: #657A62
- Deep green: #52674F
- Accent green: #718B69
- Main background: #F5F6F1
- Surface/cards: #FFFFFF
- Primary text: #303A32
- Secondary text: #6F786F
- Borders: #E2E5DC
- Soft green background: #DCE5D8
- Warning: #C49B59
- Danger: #B87568
- Information: #8299A0

Typography: Inter (headings and body)
"""

import streamlit as st
from typing import Callable, Optional, Tuple

# ---------------------------------------------------------
# Design Tokens
# ---------------------------------------------------------

COLORS = {
    # Backgrounds
    "bg_primary": "#F5F6F1",       # Main page background
    "bg_surface": "#FFFFFF",       # Cards, containers
    "bg_sidebar": "#FFFFFF",
    "bg_soft": "#DCE5D8",          # Soft green background
    # Accents
    "accent_primary": "#657A62",   # Sage green - primary actions, headings
    "accent_deep": "#52674F",      # Deep green
    "accent_light": "#718B69",     # Accent green
    "olive_muted": "#829078",      # Muted olive accent for civic-public service styling
    # Text
    "text_primary": "#303A32",     # Charcoal - headings, primary text
    "text_secondary": "#6F786F",   # Muted - secondary text, labels
    "text_inverse": "#FFFFFF",
    # Supporting surfaces
    "surface_sage": "#DCE5D8",     # Soft green
    "surface_beige": "#E9E2D5",    # Warm beige
    # Borders
    "border_light": "#E2E5DC",
    "border_focus": "#657A62",
    # Status colors
    "status_submitted": "#C49B59",
    "status_under_review": "#657A62",
    "status_approved": "#C49B59",
    "status_in_progress": "#C49B59",
    "status_resolved": "#657A62",
    "status_rejected": "#B87568",
    # Semantic colors
    "warning": "#C49B59",
    "danger": "#B87568",
    "info": "#8299A0",
}

# ---------------------------------------------------------
# CSS Injection
# ---------------------------------------------------------

PREMIUM_CSS = """
<style>
/* Import typography */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&display=swap');

/* ===== GLOBAL BASE STYLES ===== */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #F5F6F1 !important;
    color: #303A32 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    -webkit-font-smoothing: antialiased !important;
    text-rendering: optimizeLegibility !important;
}

[data-testid="stAppViewContainer"] > .main {
    background-color: #F5F6F1 !important;
    padding: 0 !important;
}

[data-testid="stHeader"] {
    background-color: #F5F6F1 !important;
    height: 0 !important;
}

/* Hide default Streamlit chrome */
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important;}
[data-testid="stDecoration"] {display: none !important;}

/* Main content area - generous spacing, constrained width */
.block-container {
    background-color: #F5F6F1 !important;
    padding: 2rem 3rem !important;
    max-width: 1200px !important;
}

/* ===== TYPOGRAPHY ===== */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', sans-serif !important;
    color: #303A32 !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em !important;
}

h1 {
    font-size: 2rem !important;
    line-height: 1.2 !important;
    margin-bottom: 0.5rem !important;
}

h2 {
    font-size: 1.45rem !important;
    margin-top: 1.5rem !important;
    margin-bottom: 1rem !important;
}

h3 {
    font-size: 1.1rem !important;
    margin-top: 1.25rem !important;
    margin-bottom: 0.75rem !important;
}

p, span, div, label {
    color: #303A32;
}

p {
    font-size: 0.96rem !important;
    line-height: 1.65 !important;
}

/* Placeholder visibility */
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: #92998F !important;
    opacity: 1 !important;
}

/* ===== BUTTONS ===== */
.stButton > button[kind="primary"] {
    background-color: #657A62 !important;
    color: #FFFFFF !important;
    border: 1px solid #657A62 !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.875rem !important;
    padding: 0.75rem 1.2rem !important;
    transition: background-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease !important;
    box-shadow: 0 1px 2px rgba(48, 58, 50, 0.08) !important;
}

.stButton > button[kind="primary"]:hover {
    background-color: #52674F !important;
    border-color: #52674F !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 10px rgba(82, 103, 79, 0.12) !important;
}

.stButton > button[kind="secondary"] {
    background-color: #FFFFFF !important;
    color: #303A32 !important;
    border: 1px solid #E2E5DC !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.75rem 1.2rem !important;
    transition: all 0.18s ease !important;
}

.stButton > button[kind="secondary"]:hover {
    background-color: #F5F6F1 !important;
    border-color: #657A62 !important;
    box-shadow: 0 2px 8px rgba(101, 122, 98, 0.08) !important;
}

/* ===== INPUT FIELDS ===== */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div,
.stNumberInput > div > div > input {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E5DC !important;
    border-radius: 10px !important;
    color: #303A32 !important;
    font-size: 0.875rem !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > div:focus,
.stNumberInput > div > div > input:focus {
    border-color: #657A62 !important;
    box-shadow: 0 0 0 3px rgba(101, 122, 98, 0.12) !important;
    outline: none !important;
}

/* ===== LABELS ===== */
label {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: #303A32 !important;
    margin-bottom: 0.25rem !important;
    text-transform: none !important;
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E2E5DC !important;
    padding: 1.5rem 1rem !important;
    width: 260px !important;
}

[data-testid="stSidebar"] .block-container {
    padding: 0 !important;
    max-width: none !important;
}

/* Sidebar brand / wordmark */
.sidebar-brand {
    font-family: 'Inter', sans-serif !important;
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    color: #657A62 !important;
    margin-bottom: 2rem !important;
    letter-spacing: -0.02em !important;
}

.sidebar-user-name {
    font-weight: 600 !important;
    color: #303A32 !important;
    font-size: 0.95rem !important;
    margin-bottom: 0.25rem !important;
}

.sidebar-user-email {
    color: #6F786F !important;
    font-size: 0.8rem !important;
    margin-bottom: 1.5rem !important;
}

.sidebar-divider {
    border: none !important;
    border-top: 1px solid #E2E5DC !important;
    margin: 1rem 0 !important;
}

.sidebar-section-label {
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: #6F786F !important;
    font-weight: 700 !important;
    margin-bottom: 0.75rem !important;
}

/* Radio navigation items */
[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    background-color: transparent !important;
    border: none !important;
    padding: 0 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    display: flex !important;
    align-items: center !important;
    padding: 0.75rem 1rem !important;
    margin-bottom: 0.375rem !important;
    border-radius: 8px !important;
    color: #6F786F !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    border: 1px solid transparent !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background-color: #DCE5D8 !important;
    color: #303A32 !important;
    border-color: #E2E5DC !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] [data-checked="true"],
[data-testid="stSidebar"] [data-baseweb="radio"] [aria-checked="true"] {
    background-color: #657A62 !important;
    color: #FFFFFF !important;
    border-color: #657A62 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] div[data-testid="stRadio"] > div {
    display: none !important;
}

/* Logout button */
[data-testid="stSidebar"] button[kind="secondary"] {
    background-color: #E9E2D5 !important;
    color: #B87568 !important;
    border: 1px solid #E2E5DC !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.625rem 1rem !important;
    border-radius: 8px !important;
    width: 100% !important;
    margin-top: 1rem !important;
}

[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background-color: #F5F6F1 !important;
    border-color: #B87568 !important;
}

/* ===== PAGE HEADER ===== */
.page-header {
    margin-bottom: 2rem !important;
}

.page-header-row {
    display: flex !important;
    align-items: center !important;
    gap: 0.75rem !important;
    margin-bottom: 0.5rem !important;
}

.page-header-icon {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 2.25rem !important;
    height: 2.25rem !important;
    background: #E9E2D5 !important;
    border: 1px solid #E2E5DC !important;
    border-radius: 0.625rem !important;
    color: #657A62 !important;
    flex-shrink: 0 !important;
}

.page-title {
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    line-height: 1.2 !important;
    color: #303A32 !important;
    margin: 0 !important;
    letter-spacing: -0.03em !important;
}

.page-subtitle {
    font-size: 0.95rem !important;
    color: #6F786F !important;
    margin: 0 !important;
}

/* ===== KPI CARDS ===== */
.kpi-grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)) !important;
    gap: 0.75rem !important;
    margin-bottom: 1.5rem !important;
}

.kpi-card {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E5DC !important;
    border-radius: 10px !important;
    padding: 1rem !important;
    display: flex !important;
    flex-direction: column !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}

.kpi-card:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
}

.kpi-card .kpi-row {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 0.5rem !important;
    margin-bottom: 0.4rem !important;
}

.kpi-card .kpi-icon {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 1.75rem !important;
    height: 1.75rem !important;
    background: #E9E2D5 !important;
    border: 1px solid #E2E5DC !important;
    border-radius: 0.5rem !important;
    color: #657A62 !important;
    flex-shrink: 0 !important;
}

.kpi-card .kpi-label {
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    color: #6F786F !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    margin-bottom: 0.4rem !important;
}

.kpi-card .kpi-value {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: #303A32 !important;
    margin: 0 !important;
    line-height: 1.2 !important;
}

/* ===== STATUS BADGES ===== */
.status-badge {
    display: inline-flex !important;
    align-items: center !important;
    gap: 0.4rem !important;
    padding: 0.375rem 0.875rem !important;
    border-radius: 9999px !important;
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.035em !important;
    border: 1px solid !important;
    line-height: 1 !important;
}

.status-badge svg {
    width: 0.8rem !important;
    height: 0.8rem !important;
    stroke: currentColor !important;
    fill: none !important;
    stroke-width: 1.8 !important;
    flex-shrink: 0 !important;
}

.status-submitted-badge {
    background-color: #E9E2D5 !important;
    color: #657A62 !important;
    border-color: #E2E5DC !important;
}
.status-under-review-badge {
    background-color: #DCE5D8 !important;
    color: #657A62 !important;
    border-color: #E2E5DC !important;
}
.status-approved-badge {
    background-color: #E9E2D5 !important;
    color: #657A62 !important;
    border-color: #E2E5DC !important;
}
.status-in-progress-badge {
    background-color: #E9E2D5 !important;
    color: #657A62 !important;
    border-color: #E2E5DC !important;
}
.status-resolved-badge {
    background-color: #DCE5D8 !important;
    color: #657A62 !important;
    border-color: #E2E5DC !important;
}
.status-rejected-badge {
    background-color: #E9E2D5 !important;
    color: #B87568 !important;
    border-color: #E2E5DC !important;
}

/* ===== COMPLAINT CARDS ===== */
.complaint-card {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E5DC !important;
    border-radius: 10px !important;
    padding: 1rem !important;
    margin-bottom: 0.75rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}

.complaint-card:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
}

.complaint-card .complaint-header {
    display: flex !important;
    justify-content: space-between !important;
    align-items: flex-start !important;
    margin-bottom: 0.5rem !important;
}

.complaint-card .complaint-title {
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    color: #303A32 !important;
    margin: 0 !important;
}

.complaint-card .complaint-meta {
    font-size: 0.8rem !important;
    color: #6F786F !important;
    margin-top: 0.25rem !important;
    line-height: 1.5 !important;
}

/* ===== FORM SECTIONS ===== */
.form-section {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E5DC !important;
    border-radius: 12px !important;
    padding: 1.25rem !important;
    margin-bottom: 1.25rem !important;
    box-shadow: 0 1px 2px rgba(48, 58, 50, 0.04) !important;
}

.form-section-title {
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    color: #303A32 !important;
    margin: 0 0 0.75rem 0 !important;
    padding-bottom: 0.5rem !important;
    border-bottom: 1px solid #E2E5DC !important;
}

/* ===== TABS ===== */
[data-testid="stTabs"] [data-testid="stTab"] {
    color: #6F786F !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 0.75rem 1rem !important;
}

[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"] {
    color: #657A62 !important;
    font-weight: 600 !important;
}

/* ===== ALERTS ===== */
.stAlert {
    border-radius: 8px !important;
    border: 1px solid #E2E5DC !important;
    background-color: #FFFFFF !important;
}

/* ===== EMPTY STATES ===== */
.empty-state {
    text-align: center !important;
    padding: 2.5rem 1rem !important;
    color: #6F786F !important;
}

.empty-state-icon {
    font-size: 2.5rem !important;
    margin-bottom: 0.75rem !important;
    opacity: 0.4 !important;
}

.empty-state-title {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #303A32 !important;
    margin-bottom: 0.375rem !important;
}

.empty-state-description {
    font-size: 0.85rem !important;
    color: #6F786F !important;
    margin-bottom: 1rem !important;
}

/* ===== DIVIDER ===== */
.section-divider {
    border: none !important;
    border-top: 1px solid #E2E5DC !important;
    margin: 1.5rem 0 !important;
}

/* ===== MAP CONTAINER ===== */
.map-container {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E5DC !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    margin-bottom: 1rem !important;
    box-shadow: 0 1px 2px rgba(48, 58, 50, 0.04) !important;
}

.map-legend {
    font-size: 0.8rem !important;
    color: #6F786F !important;
    margin-top: 0.5rem !important;
    font-weight: 500 !important;
}

/* ===== FILE UPLOADER ===== */
.stFileUploader {
    border: 2px dashed #D9DED5 !important;
    border-radius: 10px !important;
    padding: 1rem !important;
    background-color: #FFFFFF !important;
    transition: border-color 0.2s ease, background-color 0.2s ease !important;
}

.stFileUploader:hover {
    border-color: #657A62 !important;
    background-color: #F8F9F5 !important;
}

/* ===== EXPANDER ===== */
.streamlit-expanderHeader {
    background-color: #F5F6F1 !important;
    border: 1px solid #E2E5DC !important;
    border-radius: 8px !important;
    color: #303A32 !important;
    font-weight: 600 !important;
}

.streamlit-expanderContent {
    border: 1px solid #E2E5DC !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
    background-color: #FFFFFF !important;
}

/* ===== RADIO BUTTONS ===== */
[data-testid="stRadio"] > div {
    background-color: transparent !important;
}

/* ===== SECONDARY TEXT ===== */
.secondary-text {
    color: #6F786F !important;
    font-size: 0.875rem !important;
}

/* Fix metric styling */
[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E5DC !important;
    border-radius: 10px !important;
    padding: 0.75rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
}

[data-testid="stMetric"] label {
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    color: #6F786F !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: #303A32 !important;
}

/* ===== CIVICPULSE EARTH-TONE REFRESH ===== */
:root {
    --earth-bg: #F4F2EA;
    --earth-paper: #FCFBF7;
    --earth-ink: #29352D;
    --earth-muted: #72786B;
    --earth-forest: #405940;
    --earth-olive: #65744D;
    --earth-sage: #E5E8DC;
    --earth-sand: #EDE5D5;
    --earth-clay: #A96546;
    --earth-border: #E4E0D4;
    --earth-shadow: 0 12px 32px rgba(48, 57, 43, 0.06);
}

html, body, [data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main,
.block-container {
    background: var(--earth-bg) !important;
    color: var(--earth-ink) !important;
    font-family: "DM Sans", "Segoe UI", sans-serif !important;
}

[data-testid="stAppViewContainer"] {
    background-image:
        radial-gradient(ellipse at 92% 0%, rgba(205, 194, 162, 0.18), transparent 34%),
        linear-gradient(180deg, #F7F5EF 0%, var(--earth-bg) 34rem) !important;
}

.block-container {
    max-width: 1360px !important;
    padding: 4.25rem clamp(1.25rem, 4vw, 3.75rem) 3rem !important;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--earth-ink) !important;
    font-family: "DM Sans", "Segoe UI", sans-serif !important;
    letter-spacing: -0.035em !important;
}

h1, .page-title {
    font-size: clamp(1.8rem, 3vw, 2.35rem) !important;
    font-weight: 700 !important;
}

h2 {
    font-size: 1.45rem !important;
    font-weight: 650 !important;
}

p, .secondary-text, .page-subtitle {
    color: var(--earth-muted) !important;
}

[data-testid="stCaptionContainer"] p {
    color: var(--earth-muted) !important;
}

.page-header {
    margin: 0 0 2rem !important;
    padding: 0 0 1.35rem !important;
    border-bottom: 1px solid var(--earth-border) !important;
}

.page-header-kicker {
    color: var(--earth-olive) !important;
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.16em !important;
    margin-bottom: 0.65rem !important;
}

.page-header-row {
    gap: 0.85rem !important;
    margin-bottom: 0.4rem !important;
}

.page-header-icon {
    width: 2.7rem !important;
    height: 2.7rem !important;
    border-radius: 0.85rem !important;
    background: var(--earth-sage) !important;
    border: 1px solid #D9DECE !important;
    color: var(--earth-forest) !important;
}

.page-subtitle {
    font-size: 0.96rem !important;
    line-height: 1.65 !important;
    max-width: 760px !important;
}

/* Spacious, grounded navigation */
[data-testid="stSidebar"] {
    background: #F9F8F3 !important;
    border-right: 1px solid var(--earth-border) !important;
    box-shadow: 6px 0 24px rgba(48, 57, 43, 0.025) !important;
    padding: 1.5rem 1rem !important;
    width: 278px !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    color: var(--earth-ink) !important;
}

.sidebar-brand {
    color: var(--earth-forest) !important;
    font-size: 1.4rem !important;
    letter-spacing: -0.045em !important;
    margin: 0.35rem 0 1.7rem !important;
}

.sidebar-user-name {
    font-size: 0.98rem !important;
    color: var(--earth-ink) !important;
}

.sidebar-user-email, .sidebar-section-label {
    color: var(--earth-muted) !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: 0.7rem 0.85rem !important;
    margin: 0.2rem 0 !important;
    border-radius: 0.7rem !important;
    color: #626B5F !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    border: 1px solid transparent !important;
    transition: background 160ms ease, color 160ms ease, border 160ms ease !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    color: var(--earth-forest) !important;
    background: #EEF0E7 !important;
    border-color: #E1E5D9 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    color: var(--earth-forest) !important;
    background: #E7EBDD !important;
    border-color: #DCE2D3 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p,
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) span {
    color: var(--earth-forest) !important;
}

/* Buttons */
.stButton > button, [data-testid="stFormSubmitButton"] > button {
    min-height: 2.75rem !important;
    border-radius: 0.7rem !important;
    font-family: "DM Sans", "Segoe UI", sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 650 !important;
    transition: transform 160ms ease, box-shadow 160ms ease, background 160ms ease !important;
}

.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button[kind="primary"] {
    background: var(--earth-forest) !important;
    border: 1px solid var(--earth-forest) !important;
    color: #FFFDF7 !important;
    box-shadow: 0 4px 10px rgba(64, 89, 64, 0.14) !important;
}

.stButton > button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
    background: #334A36 !important;
    border-color: #334A36 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 7px 16px rgba(64, 89, 64, 0.2) !important;
}

.stButton > button[kind="secondary"],
[data-testid="stFormSubmitButton"] > button[kind="secondary"] {
    background: var(--earth-paper) !important;
    color: var(--earth-forest) !important;
    border: 1px solid #D8DCCF !important;
}

.stButton > button[kind="secondary"]:hover,
[data-testid="stFormSubmitButton"] > button[kind="secondary"]:hover {
    background: #EEF0E7 !important;
    border-color: #BFC9B6 !important;
}

/* Inputs and selection controls */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input,
[data-baseweb="select"] > div {
    background: var(--earth-paper) !important;
    border: 1px solid #DCD9CD !important;
    border-radius: 0.65rem !important;
    color: var(--earth-ink) !important;
    min-height: 2.85rem !important;
    box-shadow: inset 0 1px 2px rgba(48, 57, 43, 0.025) !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stNumberInput > div > div > input:focus,
[data-baseweb="select"] > div:focus-within {
    border-color: var(--earth-olive) !important;
    box-shadow: 0 0 0 3px rgba(101, 116, 77, 0.14) !important;
}

label, [data-testid="stWidgetLabel"] p {
    color: #384438 !important;
    font-size: 0.82rem !important;
    font-weight: 650 !important;
}

/* Surface components */
.kpi-card, .complaint-card, .form-section,
[data-testid="stMetric"], [data-testid="stForm"],
[data-testid="stExpander"] {
    background: var(--earth-paper) !important;
    border: 1px solid var(--earth-border) !important;
    border-radius: 1rem !important;
    box-shadow: var(--earth-shadow) !important;
}

.kpi-card {
    padding: 1.15rem 1.25rem !important;
    min-height: 118px !important;
    transition: transform 180ms ease, box-shadow 180ms ease !important;
}

.kpi-card:hover, .complaint-card:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 16px 34px rgba(48, 57, 43, 0.09) !important;
}

.kpi-card .kpi-label {
    color: var(--earth-muted) !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.11em !important;
}

.kpi-card .kpi-value {
    color: var(--earth-ink) !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

.kpi-card .kpi-icon {
    background: var(--earth-sage) !important;
    border: 1px solid #D9DECE !important;
    color: var(--earth-forest) !important;
}

.complaint-card {
    border-radius: 0.9rem !important;
    padding: 1.15rem 1.25rem !important;
}

.complaint-card .complaint-title {
    color: var(--earth-ink) !important;
    font-size: 1rem !important;
}

.complaint-card .complaint-meta {
    color: var(--earth-muted) !important;
}

.form-section {
    padding: 1.35rem !important;
    margin-bottom: 1.2rem !important;
    box-shadow: 0 5px 18px rgba(48, 57, 43, 0.035) !important;
}

.form-section-title {
    color: var(--earth-forest) !important;
    border-bottom-color: var(--earth-border) !important;
}

.status-submitted-badge, .status-approved-badge, .status-in-progress-badge {
    background: var(--earth-sand) !important;
    color: #765C36 !important;
    border-color: #E4D9C3 !important;
}

.status-under-review-badge, .status-resolved-badge {
    background: var(--earth-sage) !important;
    color: var(--earth-forest) !important;
    border-color: #D9DECE !important;
}

.status-rejected-badge {
    background: #F1E3DA !important;
    color: #8F503A !important;
    border-color: #E7D2C5 !important;
}

[data-testid="stTabs"] [data-testid="stTab"] {
    color: #72786B !important;
    font-weight: 600 !important;
}

[data-testid="stTabs"] {
    padding: 0.8rem 1rem 1rem !important;
    background: var(--earth-paper) !important;
    border: 1px solid var(--earth-border) !important;
    border-radius: 1rem !important;
    box-shadow: var(--earth-shadow) !important;
}

[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"] {
    color: var(--earth-forest) !important;
}

[data-testid="stTabs"] [data-testid="stTabHighlight"] {
    background: var(--earth-olive) !important;
}

[data-testid="stAlert"] {
    border-radius: 0.8rem !important;
    border: 1px solid var(--earth-border) !important;
    background: #FBFAF5 !important;
}

[data-testid="stExpander"] {
    overflow: hidden !important;
}

[data-testid="stExpander"] summary {
    background: #F8F7F1 !important;
    color: var(--earth-ink) !important;
    font-weight: 600 !important;
}

.section-divider {
    border-top-color: var(--earth-border) !important;
    margin: 1.8rem 0 !important;
}

.civic-hero {
    position: relative;
    overflow: hidden;
    padding: clamp(1.5rem, 4vw, 2.6rem);
    margin: 0 0 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.13);
    border-radius: 1.25rem;
    background:
        radial-gradient(circle at 88% 18%, rgba(205, 190, 145, 0.26), transparent 25%),
        linear-gradient(118deg, #344D3A 0%, #526849 60%, #69734E 100%);
    box-shadow: 0 16px 36px rgba(47, 68, 48, 0.16);
}

.civic-hero:after {
    content: "";
    position: absolute;
    width: 210px;
    height: 210px;
    right: -78px;
    bottom: -132px;
    border: 1px solid rgba(255, 255, 255, 0.17);
    border-radius: 50%;
    box-shadow: 0 0 0 24px rgba(255,255,255,0.035), 0 0 0 50px rgba(255,255,255,0.025);
}

.civic-hero-kicker {
    position: relative;
    z-index: 1;
    margin-bottom: 0.65rem;
    color: #D8DDC6 !important;
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.16em !important;
}

.civic-hero h2 {
    position: relative;
    z-index: 1;
    margin: 0 0 0.6rem !important;
    color: #FFFDF6 !important;
    font-family: "DM Serif Display", Georgia, serif !important;
    font-size: clamp(1.8rem, 3.4vw, 2.65rem) !important;
    font-weight: 400 !important;
    letter-spacing: -0.025em !important;
}

.civic-hero p {
    position: relative;
    z-index: 1;
    max-width: 650px;
    margin: 0 !important;
    color: #E4E6D8 !important;
    font-size: 0.95rem !important;
}

@media (max-width: 768px) {
    .block-container {
        padding: 3.75rem 1rem 2rem !important;
    }

    .page-header {
        margin-bottom: 1.4rem !important;
    }

    .kpi-card {
        min-height: 104px !important;
        padding: 0.9rem !important;
    }

    .form-section {
        padding: 1rem !important;
    }
}
</style>
"""

def inject_premium_css() -> None:
    """Inject the centralized premium CSS into the Streamlit app."""
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)


def _icon_svg(icon_name: str, color: str = "#657A62", size: int = 16) -> str:
    """Return a compact outline icon for key public-service UI labels."""
    icons = {
        "default": """
        <svg viewBox='0 0 24 24' width='{size}' height='{size}' aria-hidden='true'>
            <path d='M12 4.5v15M4.5 12h15' stroke='{color}' stroke-width='1.7' stroke-linecap='round'/>
        </svg>
        """,
        "home": """
        <svg viewBox='0 0 24 24' width='{size}' height='{size}' aria-hidden='true'>
            <path d='M4 10.5 12 4l8 6.5V18a2 2 0 0 1-2 2h-3.5v-6h-5v6H6a2 2 0 0 1-2-2z' stroke='{color}' stroke-width='1.7' fill='none' stroke-linecap='round' stroke-linejoin='round'/>
        </svg>
        """,
        "report": """
        <svg viewBox='0 0 24 24' width='{size}' height='{size}' aria-hidden='true'>
            <path d='M8 4.5h8l4 4V18a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V6.5a2 2 0 0 1 2-2z' stroke='{color}' stroke-width='1.7' fill='none' stroke-linecap='round' stroke-linejoin='round'/>
            <path d='M12 8v6M9.5 11h5' stroke='{color}' stroke-width='1.7' stroke-linecap='round'/>
        </svg>
        """,
        "complaints": """
        <svg viewBox='0 0 24 24' width='{size}' height='{size}' aria-hidden='true'>
            <path d='M7 4.5h8l4 4V18a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6.5a2 2 0 0 1 2-2z' stroke='{color}' stroke-width='1.7' fill='none' stroke-linecap='round' stroke-linejoin='round'/>
            <path d='M9.5 11.5h5M9.5 15h5' stroke='{color}' stroke-width='1.7' stroke-linecap='round'/>
        </svg>
        """,
        "dashboard": """
        <svg viewBox='0 0 24 24' width='{size}' height='{size}' aria-hidden='true'>
            <rect x='4' y='4' width='7' height='7' rx='1.5' stroke='{color}' stroke-width='1.7' fill='none'/>
            <rect x='13' y='4' width='7' height='4' rx='1.5' stroke='{color}' stroke-width='1.7' fill='none'/>
            <rect x='13' y='10' width='7' height='10' rx='1.5' stroke='{color}' stroke-width='1.7' fill='none'/>
            <rect x='4' y='13' width='7' height='7' rx='1.5' stroke='{color}' stroke-width='1.7' fill='none'/>
        </svg>
        """,
        "analytics": """
        <svg viewBox='0 0 24 24' width='{size}' height='{size}' aria-hidden='true'>
            <path d='M5 18V9M12 18V5M19 18v-8' stroke='{color}' stroke-width='1.8' stroke-linecap='round'/>
            <path d='M4 18h16' stroke='{color}' stroke-width='1.7' stroke-linecap='round'/>
        </svg>
        """,
        "profile": """
        <svg viewBox='0 0 24 24' width='{size}' height='{size}' aria-hidden='true'>
            <circle cx='12' cy='8' r='3.5' stroke='{color}' stroke-width='1.7' fill='none'/>
            <path d='M5 18c1.7-2.5 4.1-3.75 7-3.75S17.3 15.5 19 18' stroke='{color}' stroke-width='1.7' fill='none' stroke-linecap='round'/>
        </svg>
        """,
        "check": """
        <svg viewBox='0 0 24 24' width='{size}' height='{size}' aria-hidden='true'>
            <path d='M5 12.5 9.5 17 19 7.5' stroke='{color}' stroke-width='1.8' fill='none' stroke-linecap='round' stroke-linejoin='round'/>
        </svg>
        """,
        "clock": """
        <svg viewBox='0 0 24 24' width='{size}' height='{size}' aria-hidden='true'>
            <circle cx='12' cy='12' r='8' stroke='{color}' stroke-width='1.7' fill='none'/>
            <path d='M12 7.5v5l3 2' stroke='{color}' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'/>
        </svg>
        """,
        "warning": """
        <svg viewBox='0 0 24 24' width='{size}' height='{size}' aria-hidden='true'>
            <path d='M12 4.2 20 18a1.7 1.7 0 0 1-1.5 2.5h-13A1.7 1.7 0 0 1 4 18L12 4.2z' stroke='{color}' stroke-width='1.7' fill='none' stroke-linejoin='round'/>
            <path d='M12 9v4.5M12 16.5h.01' stroke='{color}' stroke-width='1.8' stroke-linecap='round'/>
        </svg>
        """,
        "location": """
        <svg viewBox='0 0 24 24' width='{size}' height='{size}' aria-hidden='true'>
            <path d='M12 20s6-5.2 6-10.2A6 6 0 1 0 6 9.8C6 14.8 12 20 12 20z' stroke='{color}' stroke-width='1.7' fill='none' stroke-linejoin='round'/>
            <circle cx='12' cy='9.8' r='2.4' stroke='{color}' stroke-width='1.7' fill='none'/>
        </svg>
        """,
        "search": """
        <svg viewBox='0 0 24 24' width='{size}' height='{size}' aria-hidden='true'>
            <circle cx='11' cy='11' r='5.5' stroke='{color}' stroke-width='1.7' fill='none'/>
            <path d='M16 16l4 4' stroke='{color}' stroke-width='1.7' stroke-linecap='round'/>
        </svg>
        """,
        "file": """
        <svg viewBox='0 0 24 24' width='{size}' height='{size}' aria-hidden='true'>
            <path d='M8 4.5h7.5L19 9v10.5A2 2 0 0 1 17 21H8a2 2 0 0 1-2-2v-12a2 2 0 0 1 2-2z' stroke='{color}' stroke-width='1.7' fill='none' stroke-linejoin='round'/>
            <path d='M15.5 4.5V9H19' stroke='{color}' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'/>
        </svg>
        """,
    }
    return icons.get(icon_name, icons["default"]).format(size=size, color=color)


# ---------------------------------------------------------
# Reusable UI Components
# ---------------------------------------------------------

def page_header(title: str, subtitle: str = "") -> None:
    """Render a clean, minimal page header with a civic-style icon."""
    normalized = (title or "").lower()
    if "dashboard" in normalized or "overview" in normalized:
        icon_name = "dashboard"
    elif "report" in normalized or "issue" in normalized:
        icon_name = "report"
    elif "complaint" in normalized or "ticket" in normalized:
        icon_name = "complaints"
    elif "analytics" in normalized or "trend" in normalized:
        icon_name = "analytics"
    elif "profile" in normalized or "account" in normalized:
        icon_name = "profile"
    else:
        icon_name = "file"

    subtitle_html = f'<p class="page-subtitle secondary-text">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="page-header">
            <div class="page-header-kicker">CIVICPULSE <span aria-hidden="true">·</span> COMMUNITY SERVICES</div>
            <div class="page-header-row">
                <span class="page-header-icon">{_icon_svg(icon_name, "#405940", 18)}</span>
                <h1 class="page-title">{title}</h1>
            </div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str) -> None:
    """Render a single KPI card with a subtle public-service icon."""
    normalized = (label or "").lower()
    if "total" in normalized or "count" in normalized or "registered" in normalized:
        icon_name = "dashboard"
    elif "resolved" in normalized or "confirmed" in normalized or "successful" in normalized:
        icon_name = "check"
    elif "review" in normalized or "pending" in normalized:
        icon_name = "clock"
    elif "rate" in normalized or "analytics" in normalized:
        icon_name = "analytics"
    elif "citizen" in normalized or "profile" in normalized:
        icon_name = "profile"
    else:
        icon_name = "file"

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-row">
                <div class="kpi-label secondary-text">{label}</div>
                <span class="kpi-icon">{_icon_svg(icon_name, "#657A62", 14)}</span>
            </div>
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
    icon_map = {
        "Submitted": "clock",
        "Under Review": "search",
        "Approved": "check",
        "In Progress": "clock",
        "Resolved": "check",
        "Rejected": "warning",
    }
    css_class = badge_map.get(status, "status-submitted-badge")
    icon_name = icon_map.get(status, "file")
    return f'<span class="status-badge {css_class}">{_icon_svg(icon_name, "currentColor", 12)}{status}</span>'


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
        coords_html = f'<br/><span style="font-size:0.8rem;color:#6F786F;">GPS: ({latitude:.4f}, {longitude:.4f})</span>'

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


def empty_state(
    icon: str,
    title: str,
    description: str,
    button_label: str = "",
    button_key: str = "",
    button_callback: Optional[Callable[..., None]] = None,
    button_callback_args: Tuple[str, ...] = (),
) -> None:
    """Render a well-designed empty state with a civic-style icon."""
    icon_map = {
        "📭": "file",
        "📊": "analytics",
        "⚠️": "warning",
        "✅": "check",
        "📍": "location",
        "🔎": "search",
        "🧾": "file",
    }
    normalized_icon = icon_map.get(icon, icon if isinstance(icon, str) and icon.lower() in {"file", "check", "analytics", "warning", "location", "search"} else "default")
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="empty-state-icon">{_icon_svg(normalized_icon, "#829078", 28)}</div>
            <h2 class="empty-state-title">{title}</h2>
            <p class="empty-state-description">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if button_label and button_key:
        if st.button(
            button_label,
            key=button_key,
            type="primary",
            use_container_width=True,
            on_click=button_callback,
            args=button_callback_args,
        ):
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
        <div style="background-color:#FFFFFF;border:1px solid #E2E5DC;border-radius:10px;padding:1.5rem;margin:1rem 0;">
            <h3 style="margin-top:0;color:#303A32;font-weight:600;">{title}</h3>
            <p style="color:#6F786F;margin-bottom:1.5rem;">{message}</p>
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
