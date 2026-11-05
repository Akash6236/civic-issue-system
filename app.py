"""
AI-Powered Civic Issue Reporting and Management System
Main Streamlit Application
"""
from datetime import datetime
from pathlib import Path
import streamlit as st
from modules.admin.complaints import (
    VALID_STATUSES,
    archive_complaint,
    edit_complaint_admin,
    get_admin_audit_logs,
    get_admin_dashboard_stats,
    get_all_complaints,
    get_archived_complaints,
    get_complaint_details_for_admin,
    update_complaint_status,
)
from modules.ai.classification import CATEGORIES, classify_complaint
from modules.ai.image_classification import (
    compare_image_and_text,
    classify_image,
    generate_suggested_description,
    generate_suggested_title,
    get_category_color,
    get_category_icon,
)
from modules.ai.duplicates import (
    get_all_duplicate_matches,
    review_duplicate_match,
)
from modules.analytics.complaint_map import (
    render_admin_complaint_map,
    render_citizen_complaint_map,
)
from modules.analytics.dashboard import (
    build_category_bar_chart,
    build_monthly_resolved_vs_received_chart,
    build_monthly_trend_chart,
    build_status_donut_chart,
    get_admin_analytics_data,
    get_citizen_analytics_data,
)
from modules.authentication.auth import (
    authenticate_user,
    create_admin_account,
    get_current_user,
    is_admin,
    is_authenticated,
    is_citizen,
    login_user,
    logout_user,
    register_citizen,
    reset_password,
)
from modules.citizen.complaints import (
    edit_complaint,
    get_citizen_complaint_details,
    get_citizen_complaints,
    get_citizen_dashboard_stats,
    get_complaint_history,
    submit_complaint,
    withdraw_complaint,
)
from modules.citizen.location_picker import render_location_picker
from modules.database import BASE_DIR, init_db
from modules.ui.theme import (
    inject_premium_css,
    page_header,
    kpi_card,
    status_badge,
    complaint_card,
    empty_state,
    form_section,
    close_form_section,
    section_divider,
    confirmation_dialog,
    portal_footer,
)
# ---------------------------------------------------------
# Page Configuration & Premium Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Civic Issue Reporting System",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="auto",
)
inject_premium_css()
def get_status_badge_html(status: str) -> str:
    """Returns an HTML status badge using the premium design system."""
    return status_badge(status)
def initialize_app():
    """Ensure database schema is verified at app launch."""
    try:
        init_db()
    except Exception as err:
        st.error(f"Database initialization error: {err}")
# Navigation Option Definitions
CITIZEN_NAV_OPTIONS = [
    "🏠 Overview",
    "📝 Report an Issue",
    "📄 My Reports",
    "📍 Track Complaints",
    "📊 My Activity",
    "👤 Profile",
]
ADMIN_NAV_OPTIONS = [
    "📊 Dashboard",
    "🗂️ All Complaints",
    "🔁 Duplicate Reports",
    "🗺️ Map View",
    "📈 Analytics",
    "🧾 Admin Activity",
]
def set_citizen_page(page_name: str) -> None:
    """Callback to switch citizen navigation page safely before widget instantiation."""
    page = normalize_nav_choice(page_name, CITIZEN_NAV_OPTIONS)
    st.session_state["_citizen_nav_page"] = page
    st.session_state["citizen_nav_radio"] = page
def set_admin_page(page_name: str) -> None:
    """Callback to switch admin navigation page safely before widget instantiation."""
    page = normalize_nav_choice(page_name, ADMIN_NAV_OPTIONS)
    st.session_state["_admin_nav_page"] = page
    st.session_state["admin_nav_radio"] = page

def normalize_nav_choice(choice: str | None, allowed_options: list[str]) -> str:
    """Normalize legacy stored nav values to the live menu labels used by the app."""
    if choice in allowed_options:
        return choice
    legacy_aliases = {
        "Overview": "🏠 Overview",
        "Report an Issue": "📝 Report an Issue",
        "My Reports": "📄 My Reports",
        "Track Complaints": "📍 Track Complaints",
        "My Activity": "📊 My Activity",
        "Profile": "👤 Profile",
        "Dashboard": "📊 Dashboard",
        "All Complaints": "🗂️ All Complaints",
        "Pending Review": "🕒 Pending Review",
        "Duplicate Reports": "🔁 Duplicate Reports",
        "Map View": "🗺️ Map View",
        "Analytics": "📈 Analytics",
        "Resolved Reports": "✅ Resolved Reports",
        "Archived Reports": "🗄️ Archived Reports",
        "Admin Activity": "🧾 Admin Activity",
        "Settings": "⚙️ Settings",
    }
    if choice in legacy_aliases:
        return legacy_aliases[choice]
    return allowed_options[0]
# ---------------------------------------------------------
# View: Public Authentication (Login / Register)
# ---------------------------------------------------------
def render_auth_view():
    """Renders the public login and citizen registration interface."""
    page_header(
        "CivicPulse",
        "A clearer way to share local concerns, follow progress, and help your neighbourhood thrive.",
    )
    tab_login, tab_register, tab_admin, tab_forgot = st.tabs(
        ["Sign In", "Create Citizen Account", "Create Admin Account", "Forgot Password"]
    )
    # TAB 1: LOGIN
    with tab_login:
        st.subheader("Access Your Account")
        st.caption("Enter your registered credentials to access your dashboard.")
        with st.form("login_form", clear_on_submit=False):
            login_email = st.text_input("Email Address", placeholder="name@example.com").strip()
            login_password = st.text_input("Password", type="password", placeholder="Enter your password")
            login_submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
            if login_submitted:
                if not login_email or not login_password:
                    st.error("Please enter both email and password.")
                else:
                    success, message, user_data = authenticate_user(login_email, login_password)
                    if success and user_data:
                        login_user(user_data)
                        st.success(f"Welcome back, {user_data['full_name']}!")
                        st.rerun()
                    else:
                        st.error(message)
        st.info(
            "Municipal Authority Access: Municipal administrators use designated credentials. "
            "Staff accounts are provisioned securely by IT administration.",
        )
    # TAB 2: CITIZEN REGISTRATION
    with tab_register:
        st.subheader("Citizen Registration")
        st.caption("Sign up to report civic issues and receive status updates in your ward.")
        with st.form("register_form", clear_on_submit=False):
            reg_name = st.text_input("Full Name", placeholder="e.g., John Doe")
            reg_email = st.text_input("Email Address", placeholder="e.g., john@example.com")
            reg_phone = st.text_input("Phone Number (Optional)", placeholder="e.g., 9876543210")
            reg_password = st.text_input(
                "Password",
                type="password",
                help="Must be at least 8 characters and include at least one letter and one number.",
            )
            reg_confirm_password = st.text_input("Confirm Password", type="password")
            reg_submitted = st.form_submit_button("Register Account", use_container_width=True, type="primary")
            if reg_submitted:
                success, message, user_id = register_citizen(
                    full_name=reg_name,
                    email=reg_email,
                    phone=reg_phone,
                    password=reg_password,
                    confirm_password=reg_confirm_password,
                )
                if success:
                    st.success(f"{message} Please switch to the 'Sign In' tab to log in.")
                else:
                    st.error(message)
        st.caption("Public registration creates Citizen accounts only. Administrator roles are restricted.")
    # TAB 3: CREATE ADMIN ACCOUNT
    with tab_admin:
        st.subheader("Create Administrator Account")
        st.caption("Create a new administrator account using a setup code.")
        with st.form("create_admin_form", clear_on_submit=False):
            admin_name = st.text_input("Full Name", placeholder="e.g., Admin Name")
            admin_email = st.text_input("Admin Email", placeholder="e.g., admin@city.gov")
            admin_password = st.text_input(
                "Password",
                type="password",
                help="Must be at least 8 characters and include at least one letter and one number.",
            )
            admin_confirm = st.text_input("Confirm Password", type="password")
            admin_setup_code = st.text_input(
                "Setup Code",
                type="password",
                help="Enter the administrator setup code provided by IT.",
            )
            admin_submitted = st.form_submit_button("Create Admin Account", use_container_width=True, type="primary")
            if admin_submitted:
                success, message, user_id = create_admin_account(
                    full_name=admin_name,
                    email=admin_email,
                    password=admin_password,
                    confirm_password=admin_confirm,
                    setup_code=admin_setup_code,
                )
                if success:
                    st.success(f"{message} Please switch to the 'Sign In' tab to log in.")
                else:
                    st.error(message)
        st.caption("Setup code required. Contact IT administration for the code.")
    # TAB 4: FORGOT PASSWORD
    with tab_forgot:
        st.subheader("Reset Password")
        st.caption("Enter your email and set a new password.")
        with st.form("forgot_password_form", clear_on_submit=False):
            forgot_email = st.text_input("Email Address", placeholder="name@example.com").strip()
            forgot_new_password = st.text_input(
                "New Password",
                type="password",
                help="Must be at least 8 characters and include at least one letter and one number.",
            )
            forgot_confirm = st.text_input("Confirm New Password", type="password")
            forgot_submitted = st.form_submit_button("Reset Password", use_container_width=True, type="primary")
            if forgot_submitted:
                if not forgot_email or not forgot_new_password or not forgot_confirm:
                    st.error("All fields are required.")
                else:
                    success, message = reset_password(
                        email=forgot_email,
                        new_password=forgot_new_password,
                        confirm_password=forgot_confirm,
                    )
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
        st.caption("Works for both citizen and administrator accounts.")
# ---------------------------------------------------------
# View: Citizen - Overview Dashboard
# ---------------------------------------------------------
def render_citizen_dashboard(user: dict):
    """Overview dashboard for citizens."""
    page_header(
        "Citizen Dashboard",
        "Welcome back. Here is an overview of your reported civic issues.",
    )
    st.markdown(
        """
        <section class="civic-hero">
            <div class="civic-hero-kicker">YOUR NEIGHBOURHOOD, YOUR VOICE</div>
            <h2>Small reports. Real community change.</h2>
            <p>Share what needs attention nearby and follow each report as it moves toward resolution.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    stats = get_citizen_dashboard_stats(user["id"])
    # KPI grid
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    kpi_card("Total Filed", str(stats["total"]))
    kpi_card("Submitted", str(stats["submitted"]))
    kpi_card("Under Review", str(stats["under_review"]))
    kpi_card("In Progress", str(stats["in_progress"]))
    kpi_card("Resolved", str(stats["resolved"]))
    st.markdown('</div>', unsafe_allow_html=True)
    section_divider()
    # Action row
    col_action1, col_action2, col_action3 = st.columns(3)
    with col_action1:
        st.button(
            "Report a New Civic Issue",
            type="primary",
            use_container_width=True,
            on_click=set_citizen_page,
            args=("Report an Issue",),
        )
    with col_action2:
        st.button(
            "View My Complaints History",
            use_container_width=True,
            on_click=set_citizen_page,
            args=("My Reports",),
        )
    with col_action3:
        st.button(
            "My Activity",
            use_container_width=True,
            on_click=set_citizen_page,
            args=("My Activity",),
        )
    section_divider()
    st.subheader("Recent Submissions")
    recent_complaints = get_citizen_complaints(user["id"])[:3]
    if not recent_complaints:
        empty_state(
            "📭",
            "No complaints yet",
            "You haven't reported any civic issues. Click 'Report a New Civic Issue' above to submit your first report.",
            "Report a New Civic Issue",
            "empty_state_report",
            button_callback=set_citizen_page,
            button_callback_args=("Report an Issue",),
        )
    else:
        for c in recent_complaints:
            complaint_card(
                complaint_id=c["id"],
                title=c["title"],
                status=c["status"],
                category=c["category"],
                location_address=c["location_address"],
                created_at=c["created_at"],
                latitude=c.get("latitude"),
                longitude=c.get("longitude"),
            )
# ---------------------------------------------------------
# View: Citizen - Report Issue Form (with AI Classification)
# ---------------------------------------------------------
def render_citizen_report_issue(user: dict):
    """Complaint submission form for citizens with AI-assisted classification."""
    if st.session_state.pop("_clear_citizen_report_form", False):
        state_prefixes = (
            "issue_input_",
            "loc_picker_",
            "address_search_",
            "map_link_",
            "gps_",
            "location_map_",
        )
        for key in tuple(st.session_state):
            if key.startswith(state_prefixes):
                st.session_state.pop(key, None)

    page_header(
        "Report a Civic Issue",
        "Provide details and photo proof to help municipal crews inspect and resolve the problem.",
    )
    # Step 1: Location selection (map-first)
    form_section("Step 1 — Select Location")
    st.caption("Tell us where the issue is located so crews can find it quickly.")
    location_data = render_location_picker()
    close_form_section()
    # Step 2: Issue details
    form_section("Step 2 — Describe the Issue")
    st.caption("A clear title and description help us route your report to the right team.")
    title = st.text_input(
        "Complaint Title",
        placeholder="e.g., Deep pothole causing vehicular congestion",
        help="Brief summary of the issue.",
        key="issue_input_title",
    )
    description = st.text_area(
        "Detailed Description",
        placeholder="Explain the severity, impact, and exact spot of the civic issue...",
        height=110,
        key="issue_input_desc",
    )
    # Image uploader
    upload_img = st.file_uploader(
        "Attach Photograph (Optional)",
        type=["jpg", "jpeg", "png", "webp"],
        help="Upload an on-site photo (Max 5MB; JPG, PNG, WEBP).",
        key="issue_input_image",
    )
    # Image classification (only if image uploaded)
    img_cat = None
    img_conf = None
    img_scores = {}
    pil_img = None
    if upload_img is not None:
        img_cat, img_conf, img_scores, pil_img = classify_image(upload_img)
        if pil_img is not None:
            st.image(pil_img, caption="Uploaded Photograph", use_container_width=True)
    # Real-Time AI Category Suggestion Engine
    predicted_cat, confidence_score, all_scores = classify_complaint(title, description)
    # Initialize AI suggestion variables
    ai_suggestion = predicted_cat
    ai_confidence = confidence_score
    # Combined AI suggestion display
    if title or description or upload_img is not None:
        ai_suggestion = predicted_cat
        ai_confidence = confidence_score
        ai_source = "Text analysis"
        if img_cat is not None and img_conf is not None:
            if img_conf >= 0.40:
                ai_suggestion = img_cat
                ai_confidence = img_conf
                ai_source = "Image analysis"
            else:
                ai_suggestion = predicted_cat
                ai_confidence = confidence_score
                ai_source = "Text analysis (image uncertain)"
        comparison = (
            compare_image_and_text(img_cat, predicted_cat, img_conf)
            if upload_img is not None
            else {"warning_message": None}
        )
        ai_box_html = f"""
        <div style="background-color:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;padding:1rem;margin:1rem 0;">
            <span style="font-weight:700;color:#1E293B;">AI Category Recommendation:</span>
            <span style="font-size:1.05rem;font-weight:800;color:#1E293B;margin-left:0.4rem;">{ai_suggestion}</span>
            <span style="color:#64748B;margin-left:0.5rem;font-size:0.9rem;">(Confidence: {int(ai_confidence * 100)}%, {ai_source})</span>
        """
        if comparison["warning_message"]:
            ai_box_html += f"""
            <div style="margin-top:0.5rem;padding:0.5rem;background-color:#FFFFFF;border:1px solid #E2E8F0;border-radius:8px;font-size:0.85rem;color:#1E293B;">
                <span style="font-weight:700;">⚠</span> {comparison["warning_message"]}
            </div>
            """
        ai_box_html += f"""
            <div style="font-size:0.82rem;color:#64748B;margin-top:0.25rem;">
                Local analysis suggests <em>{ai_suggestion}</em>. You can confirm or override this category below.
            </div>
        </div>
        """
        st.markdown(ai_box_html, unsafe_allow_html=True)
        # Show suggested title and description without replacing citizen input.
        suggested_title = generate_suggested_title(img_cat if img_cat else predicted_cat)
        st.markdown("**Suggested Title:**")
        st.caption(suggested_title)
        st.markdown("**Suggested Description:**")
        st.caption(generate_suggested_description(img_cat, img_conf))
    close_form_section()
    # Step 3: Category selection
    form_section("Step 3 — Confirm Category")
    st.caption("You may manually adjust the category if the AI suggestion differs.")
    default_cat_idx = 0
    if ai_suggestion in CATEGORIES:
        default_cat_idx = CATEGORIES.index(ai_suggestion)
    category = st.selectbox(
        "Selected Category",
        CATEGORIES,
        index=default_cat_idx,
        help="You may manually adjust the category if the AI suggestion differs.",
    )
    close_form_section()
    # Submission guard
    if "_complaint_submission_guard" not in st.session_state:
        st.session_state["_complaint_submission_guard"] = None
    if "_complaint_submission_result" not in st.session_state:
        st.session_state["_complaint_submission_result"] = None
    # If a previous submission completed, show result and clear guard
    if st.session_state["_complaint_submission_result"] is not None:
        success, message, complaint_id = st.session_state["_complaint_submission_result"]
        st.session_state["_complaint_submission_result"] = None
        st.session_state["_complaint_submission_guard"] = None
        if success:
            st.success(message)
        else:
            st.error(message)
    # Submission button
    is_processing = st.session_state["_complaint_submission_guard"] is not None
    submit_btn = st.button(
        "Submit Civic Complaint",
        type="primary",
        use_container_width=True,
        disabled=is_processing,
        key="submit_citizen_complaint_btn",
    )
    if submit_btn and not is_processing:
        # Validate required fields before submission
        if not title.strip():
            st.error("Complaint title is required.")
        elif not category.strip():
            st.error("Please select a category.")
        elif not description.strip():
            st.error("Detailed description is required.")
        elif not location_data["location_address"].strip():
            st.error("Location address or landmark is required.")
        else:
            import uuid as uuid_module
            st.session_state["_complaint_submission_guard"] = str(uuid_module.uuid4())
            with st.spinner("Submitting your complaint..."):
                success, message, complaint_id = submit_complaint(
                    user_id=user["id"],
                    title=title,
                    category=category,
                    description=description,
                    location_address=location_data["location_address"],
                    uploaded_image=upload_img,
                    latitude=location_data["latitude"],
                    longitude=location_data["longitude"],
                    location_source=location_data["location_source"],
                    location_confirmed=1 if location_data["location_confirmed"] else 0,
                    ai_category=ai_suggestion,
                    ai_confidence=ai_confidence,
                )
            st.session_state["_complaint_submission_result"] = (success, message, complaint_id)
            if success:
                st.session_state["_clear_citizen_report_form"] = True
            st.session_state["_complaint_submission_guard"] = None
            st.rerun()
# ---------------------------------------------------------
# View: Citizen - My Complaints
# ---------------------------------------------------------
def render_citizen_my_complaints(user: dict):
    """Lists only the logged-in citizen's complaints with filters and history."""
    page_header(
        "My Reports",
        "Track resolution progress and municipal remarks for your reported complaints.",
    )
    f1, f2, f3 = st.columns([1.5, 1.2, 1.2])
    with f1:
        search_kw = st.text_input("Search My Issues", placeholder="Title, description, address...")
    with f2:
        cat_filter = st.selectbox("Category", ["All"] + CATEGORIES)
    with f3:
        status_filter = st.selectbox(
            "Status",
            ["All", "Submitted", "Under Review", "Approved", "In Progress", "Resolved", "Rejected"],
        )
    complaints = get_citizen_complaints(
        user_id=user["id"],
        status_filter=status_filter,
        category_filter=cat_filter,
        search_query=search_kw,
    )
    st.markdown(f"**Found {len(complaints)} complaint(s)**")
    if not complaints:
        empty_state(
            "📭",
            "No complaints found",
            "No complaints match your selected filters.",
        )
        return
    for c in complaints:
        complaint_card(
            complaint_id=c["id"],
            title=c["title"],
            status=c["status"],
            category=c["category"],
            location_address=c["location_address"],
            created_at=c["created_at"],
            latitude=c.get("latitude"),
            longitude=c.get("longitude"),
            image_path=c.get("image_path"),
            show_image=False,
        )
        with st.expander(f"View details for #{c['id']}", expanded=False):
            col_info, col_img = st.columns([1.4, 1.0])
            with col_info:
                st.markdown(f"**Status:** {get_status_badge_html(c['status'])}", unsafe_allow_html=True)
                st.markdown(f"**Category:** `{c['category']}`")
                if c.get("ai_category"):
                    conf_pct = int((c.get("ai_confidence") or 0.0) * 100)
                    st.caption(f"AI Tag: {c['ai_category']} ({conf_pct}% confidence)")
                st.markdown(f"**Location:** {c['location_address']}")
                if c["latitude"] is not None and c["longitude"] is not None:
                    st.caption(f"GPS: ({c['latitude']:.5f}, {c['longitude']:.5f})")
                st.markdown(f"**Submitted Date:** {c['created_at'][:19]}")
                st.markdown(f"**Last Updated:** {c['updated_at'][:19]}")
                st.markdown("---")
                st.markdown(f"**Description:**\n{c['description']}")
            with col_img:
                if c["image_path"]:
                    img_file = BASE_DIR / c["image_path"]
                    if img_file.exists():
                        st.image(str(img_file), caption="Complaint Photograph", use_container_width=True)
                    else:
                        st.caption("Attached image could not be loaded from storage.")
                else:
                    st.caption("No photograph attached to this complaint.")
            st.markdown("#### Resolution Progress & Status History")
            history = get_complaint_history(c["id"])
            if history:
                for h in history:
                    old_st_text = h["old_status"] if h["old_status"] else "Initial"
                    st.markdown(
                        f"""
                        <div style="border-left:3px solid #BFDBFE;padding-left:0.75rem;margin-bottom:0.75rem;">
                            <strong>{old_st_text} &rarr; {h['new_status']}</strong>
                            <span style="color:#64748B;font-size:0.85rem;">({h['changed_at'][:16]})</span><br/>
                            <span style="color:#1E293B;font-size:0.85rem;">By {h['changed_by_name']} ({h['changed_by_role'].capitalize()})</span><br/>
                            <em style="color:#1E293B;font-size:0.85rem;">"{h['remarks'] or 'No remarks provided.'}"</em>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No history records available.")
            # Edit and Withdraw options (only for eligible statuses)
            is_editable = c["status"] in ("Submitted", "Under Review")
            is_withdrawable = c["status"] in ("Submitted", "Under Review")
            if is_editable or is_withdrawable:
                st.markdown("#### Manage Complaint")
                if is_editable:
                    with st.form(f"edit_form_{c['id']}", clear_on_submit=False):
                        st.markdown("**Edit Complaint**")
                        edit_title = st.text_input(
                            "Title",
                            value=c["title"],
                            key=f"edit_title_{c['id']}",
                        )
                        edit_desc = st.text_area(
                            "Description",
                            value=c["description"],
                            height=80,
                            key=f"edit_desc_{c['id']}",
                        )
                        edit_cat = st.selectbox(
                            "Category",
                            CATEGORIES,
                            index=CATEGORIES.index(c["category"]) if c["category"] in CATEGORIES else 0,
                            key=f"edit_cat_{c['id']}",
                        )
                        edit_loc = st.text_input(
                            "Location",
                            value=c["location_address"],
                            key=f"edit_loc_{c['id']}",
                        )
                        edit_submit = st.form_submit_button(
                            "Update Complaint", type="primary", use_container_width=True
                        )
                        if edit_submit:
                            ok, msg = edit_complaint(
                                complaint_id=c["id"],
                                user_id=user["id"],
                                title=edit_title,
                                category=edit_cat,
                                description=edit_desc,
                                location_address=edit_loc,
                            )
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                if is_withdrawable:
                    with st.form(f"withdraw_form_{c['id']}", clear_on_submit=False):
                        st.markdown("**Withdraw Complaint**")
                        st.caption(
                            "Withdrawing will mark this complaint as rejected with your reason recorded. "
                            "The record will be preserved for audit purposes."
                        )
                        withdraw_reason = st.text_input(
                            "Withdrawal Reason",
                            placeholder="Why are you withdrawing this complaint?",
                            key=f"withdraw_reason_{c['id']}",
                        )
                        withdraw_submit = st.form_submit_button(
                            "Withdraw Complaint", use_container_width=True
                        )
                        if withdraw_submit:
                            if not withdraw_reason.strip():
                                st.error("A withdrawal reason is required.")
                            else:
                                ok, msg = withdraw_complaint(
                                    complaint_id=c["id"],
                                    user_id=user["id"],
                                    reason=withdraw_reason,
                                )
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
# ---------------------------------------------------------
# View: Citizen - My Analytics
# ---------------------------------------------------------
def render_citizen_analytics(user: dict):
    """Visual analytics charts for citizen's reported issues."""
    page_header(
        "My Activity",
        "Interactive metrics and status breakdowns of your submitted civic issues.",
    )
    data = get_citizen_analytics_data(user["id"])
    kpi_card("Total Complaints Filed", str(data["total_complaints"]))
    resolved_count = sum(r["count"] for r in data["status_distribution"] if r["status"] == "Resolved")
    kpi_card("Successfully Resolved", str(resolved_count))
    kpi_card("Resolution Rate", f"{data['resolution_rate']}%")
    section_divider()
    if data["total_complaints"] == 0:
        empty_state(
            "📭",
            "No complaint data yet",
            "Submit a complaint to view your personal analytics!",
        )
        return
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        fig_status = build_status_donut_chart(data["status_distribution"], title="My Issues: Status Breakdown")
        st.plotly_chart(fig_status, use_container_width=True)
    with col_chart2:
        fig_cat = build_category_bar_chart(data["category_distribution"], title="My Issues: Category Breakdown")
        st.plotly_chart(fig_cat, use_container_width=True)
    if data["monthly_trend"]:
        fig_trend = build_monthly_trend_chart(data["monthly_trend"], title="My Monthly Submissions Trend")
        st.plotly_chart(fig_trend, use_container_width=True)
# ---------------------------------------------------------
# View: Citizen - Profile
# ---------------------------------------------------------
def render_citizen_profile(user: dict):
    """Citizen profile page showing account details and statistics."""
    page_header(
        "Profile",
        "Manage your account details and view your reporting summary.",
    )
    stats = get_citizen_dashboard_stats(user["id"])
    col_profile, col_stats = st.columns([1.4, 1])
    with col_profile:
        form_section("Account Details")
        st.markdown(f"**Name:** {user['full_name']}")
        st.markdown(f"**Email:** {user['email']}")
        st.markdown(f"**Phone:** {user.get('phone') or 'Not provided'}")
        st.markdown(f"**Role:** {user.get('role', 'citizen').capitalize()}")
        st.markdown(f"**Member Since:** {user.get('created_at', 'N/A')[:10]}")
        close_form_section()
    with col_stats:
        form_section("Your Summary")
        kpi_card("Total Filed", str(stats["total"]))
        kpi_card("Submitted", str(stats["submitted"]))
        kpi_card("Resolved", str(stats["resolved"]))
        resolved_count = sum(r["count"] for r in get_citizen_analytics_data(user["id"])["status_distribution"] if r["status"] == "Resolved")
        rate = 0.0
        if stats["total"] > 0:
            rate = round((resolved_count / stats["total"]) * 100.0, 1)
        kpi_card("Resolution Rate", f"{rate}%")
        close_form_section()
# ---------------------------------------------------------
# View: Admin - Operations Overview
# ---------------------------------------------------------
def render_admin_dashboard(user: dict):
    """Overview dashboard for municipal administrators."""
    page_header(
        "Municipal Dashboard",
        f"Administrator: {user['full_name']} | Municipal Operations Command",
    )
    st.markdown(
        """
        <section class="admin-hero">
            <div class="admin-hero-kicker">CITY OPERATIONS · SERVICE DELIVERY</div>
            <h2>Every report is a chance to improve the community.</h2>
            <p>Review incoming concerns, coordinate action, and keep residents informed from one municipal workspace.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    stats = get_admin_dashboard_stats()
    # Compact KPI grid
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    kpi_card("Total Tickets", str(stats["total"]))
    kpi_card("New Submitted", str(stats["submitted"]))
    kpi_card("Under Review / Active", str(stats["under_review"] + stats["in_progress"]))
    kpi_card("Resolved", str(stats["resolved"]))
    kpi_card("Registered Citizens", str(stats["total_citizens"]))
    st.markdown('</div>', unsafe_allow_html=True)
    section_divider()
    col_left, col_right = st.columns([1.5, 1])
    with col_left:
        st.subheader("Quick Actions")
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            st.button(
                "Open Complaint Triage",
                type="primary",
                use_container_width=True,
                on_click=set_admin_page,
                args=("All Complaints",),
            )
        with btn_c2:
            st.button(
                "Inspect Duplicate Reports",
                use_container_width=True,
                on_click=set_admin_page,
                args=("Duplicate Reports",),
            )
        section_divider()
        st.subheader("Recent Submissions Requiring Triage")
        pending_complaints = get_all_complaints(status="Submitted")[:5]
        if not pending_complaints:
            st.success("No newly submitted complaints awaiting initial triage.")
        else:
            for p in pending_complaints:
                complaint_card(
                    complaint_id=p["id"],
                    title=p["title"],
                    status=p["status"],
                    category=p["category"],
                    location_address=p["location_address"],
                    created_at=p["created_at"],
                )
    with col_right:
        st.subheader("Recent Admin Activity")
        logs = get_admin_audit_logs(limit=5)
        if not logs:
            st.info("No administrative actions recorded yet.")
        else:
            for l in logs:
                st.markdown(
                    f"""
                    <div style="border-left:3px solid #3B82F6;padding-left:0.75rem;margin-bottom:0.75rem;">
                        <span style="color:#64748B;font-size:0.85rem;">{l['action_timestamp'][:16]}</span><br/>
                        <strong style="color:#1E293B;">{l['admin_name']}</strong>: {l['action_type']}<br/>
                        <span style="color:#1E293B;font-size:0.85rem;">{l['action_details']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
# ---------------------------------------------------------
# View: Admin - Pending Review
# ---------------------------------------------------------
def render_admin_pending_review(user: dict):
    """Shows complaints pending initial review (Submitted or Under Review)."""
    page_header(
        "Pending Review",
        "Complaints awaiting initial triage and review.",
    )
    complaints = get_all_complaints(status="Submitted") + get_all_complaints(status="Under Review")
    if not complaints:
        empty_state("📭", "No pending complaints", "All complaints have been reviewed.")
        return
    st.markdown(f"**Found {len(complaints)} pending complaint(s)**")
    for c in complaints:
        complaint_card(
            complaint_id=c["id"],
            title=c["title"],
            status=c["status"],
            category=c["category"],
            location_address=c["location_address"],
            created_at=c["created_at"],
            latitude=c.get("latitude"),
            longitude=c.get("longitude"),
            image_path=c.get("image_path"),
            show_image=False,
        )
# ---------------------------------------------------------
# View: Admin - Resolved Reports
# ---------------------------------------------------------
def render_admin_resolved_reports(user: dict):
    """Shows resolved complaints."""
    page_header(
        "Resolved Reports",
        "Complaints that have been resolved.",
    )
    complaints = get_all_complaints(status="Resolved")
    if not complaints:
        empty_state("📭", "No resolved complaints", "No complaints have been resolved yet.")
        return
    st.markdown(f"**Found {len(complaints)} resolved complaint(s)**")
    for c in complaints:
        complaint_card(
            complaint_id=c["id"],
            title=c["title"],
            status=c["status"],
            category=c["category"],
            location_address=c["location_address"],
            created_at=c["created_at"],
            latitude=c.get("latitude"),
            longitude=c.get("longitude"),
            image_path=c.get("image_path"),
            show_image=False,
        )
# ---------------------------------------------------------
# View: Admin - Archived Reports
# ---------------------------------------------------------
def render_admin_archived_reports(user: dict):
    """Shows archived complaints."""
    page_header(
        "Archived Reports",
        "Complaints that have been archived by administrators.",
    )
    complaints = get_archived_complaints()
    if not complaints:
        empty_state("📭", "No archived complaints", "No complaints have been archived.")
        return
    st.markdown(f"**Found {len(complaints)} archived complaint(s)**")
    for c in complaints:
        complaint_card(
            complaint_id=c["id"],
            title=c["title"],
            status=c["status"],
            category=c["category"],
            location_address=c["location_address"],
            created_at=c["created_at"],
            latitude=c.get("latitude"),
            longitude=c.get("longitude"),
            image_path=c.get("image_path"),
            show_image=False,
        )
# ---------------------------------------------------------
# View: Admin - Settings
# ---------------------------------------------------------
def render_admin_settings(user: dict):
    """Admin settings page."""
    page_header(
        "Settings",
        "System configuration and admin preferences.",
    )
    st.info("Settings panel coming soon. Admin account management is available via utils/reset_admin.py.")
# ---------------------------------------------------------
# View: Admin - Complaint Management
# ---------------------------------------------------------
def render_admin_complaint_management(user: dict):
    """Complaint triage, filtering, inspection, and status updates for administrators."""
    page_header(
        "Complaint Management",
        "Inspect citizen tickets, verify photo proof, and update workflow statuses.",
    )
    col_s1, col_s2, col_s3, col_s4 = st.columns([1.5, 1, 1, 1])
    with col_s1:
        admin_search = st.text_input("Search Complaints", placeholder="ID, title, citizen, address...")
    with col_s2:
        admin_cat = st.selectbox("Category Filter", ["All"] + CATEGORIES, key="admin_cat_filter")
    with col_s3:
        admin_status = st.selectbox("Status Filter", ["All"] + VALID_STATUSES, key="admin_st_filter")
    with col_s4:
        sort_order = st.selectbox("Sort By", ["Newest First", "Oldest First"])
    all_complaints = get_all_complaints(
        search_query=admin_search,
        category=admin_cat,
        status=admin_status,
    )
    if sort_order == "Oldest First":
        all_complaints.reverse()
    st.markdown(f"**Found {len(all_complaints)} complaint(s)**")
    if not all_complaints:
        empty_state(
            "📭",
            "No complaints found",
            "No complaints match the selected filters.",
        )
        return
    col_list, col_inspect = st.columns([1.2, 1.8])
    with col_list:
        st.subheader("Complaints Queue")
        complaint_options = {
            f"#{c['id']} | {c['category']} | {c['status']} - {c['title'][:35]}": c["id"]
            for c in all_complaints
        }
        selected_label = st.radio(
            "Select a complaint to inspect:",
            options=list(complaint_options.keys()),
            label_visibility="collapsed",
        )
        selected_id = complaint_options[selected_label]
    with col_inspect:
        complaint_detail = get_complaint_details_for_admin(selected_id)
        if not complaint_detail:
            st.error("Selected complaint could not be loaded.")
            return
        st.subheader(f"Ticket #{complaint_detail['id']}: {complaint_detail['title']}")
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown(f"**Status:** {get_status_badge_html(complaint_detail['status'])}", unsafe_allow_html=True)
        with r2:
            st.markdown(f"**Category:** `{complaint_detail['category']}`")
        with r3:
            st.markdown(f"**Date:** {complaint_detail['created_at'][:16]}")
        if complaint_detail.get("ai_category"):
            conf_pct = int((complaint_detail.get("ai_confidence") or 0.0) * 100)
            st.caption(f"AI Categorization: **{complaint_detail['ai_category']}** ({conf_pct}% confidence)")
        st.markdown("---")
        with st.container():
            st.markdown(
                f"""
                <div style="background-color:#F8FAFC;padding:0.75rem;border-radius:10px;border:1px solid #E2E8F0;margin-bottom:1rem;">
                    <strong>Citizen:</strong> {complaint_detail['citizen_name']} | 
                    <strong>Email:</strong> {complaint_detail['citizen_email']} | 
                    <strong>Phone:</strong> {complaint_detail['citizen_phone'] or 'Not provided'}
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown(f"**Location:** {complaint_detail['location_address']}")
        if complaint_detail["latitude"] is not None and complaint_detail["longitude"] is not None:
            st.caption(f"Coordinates: ({complaint_detail['latitude']:.5f}, {complaint_detail['longitude']:.5f})")
        st.markdown(f"**Description:**\n{complaint_detail['description']}")
        if complaint_detail["image_path"]:
            img_path = BASE_DIR / complaint_detail["image_path"]
            if img_path.exists():
                st.image(str(img_path), caption="Citizen Uploaded Photograph", use_container_width=True)
            else:
                st.caption("Photo file not found on disk.")
        else:
            st.caption("No photo was submitted with this issue.")
        st.markdown("---")
        st.markdown("### Update Complaint Status")
        current_st = complaint_detail["status"]
        with st.form(f"update_status_form_{selected_id}", clear_on_submit=False):
            curr_idx = VALID_STATUSES.index(current_st) if current_st in VALID_STATUSES else 0
            new_selected_status = st.selectbox(
                "New Status",
                VALID_STATUSES,
                index=curr_idx,
            )
            admin_remarks = st.text_area(
                "Administrative Remarks / Action Taken",
                placeholder="e.g., Verified on-site. Field crew dispatched for repair.",
                height=90,
            )
            update_submit = st.form_submit_button("Apply Status Change", type="primary", use_container_width=True)
            if update_submit:
                if new_selected_status == current_st:
                    st.warning(f"Complaint is already in '{current_st}' status. Select a different status to update.")
                elif not admin_remarks or not admin_remarks.strip():
                    st.error("Please provide remarks explaining the status change.")
                else:
                    up_ok, up_msg = update_complaint_status(
                        complaint_id=selected_id,
                        admin_id=user["id"],
                        new_status=new_selected_status,
                        remarks=admin_remarks,
                    )
                    if up_ok:
                        st.success(up_msg)
                        st.rerun()
                    else:
                        st.error(up_msg)
        st.markdown("---")
        # Admin Edit Complaint Details
        st.markdown("### Edit Complaint Details")
        with st.form(f"edit_admin_form_{selected_id}", clear_on_submit=False):
            edit_title = st.text_input(
                "Title",
                value=complaint_detail["title"],
                key=f"admin_edit_title_{selected_id}",
            )
            edit_cat = st.selectbox(
                "Category",
                CATEGORIES,
                index=CATEGORIES.index(complaint_detail["category"]) if complaint_detail["category"] in CATEGORIES else 0,
                key=f"admin_edit_cat_{selected_id}",
            )
            edit_desc = st.text_area(
                "Description",
                value=complaint_detail["description"],
                height=80,
                key=f"admin_edit_desc_{selected_id}",
            )
            edit_loc = st.text_input(
                "Location",
                value=complaint_detail["location_address"],
                key=f"admin_edit_loc_{selected_id}",
            )
            edit_admin_submit = st.form_submit_button(
                "Update Complaint Details", type="primary", use_container_width=True
            )
            if edit_admin_submit:
                ok, msg = edit_complaint_admin(
                    complaint_id=selected_id,
                    admin_id=user["id"],
                    title=edit_title,
                    category=edit_cat,
                    description=edit_desc,
                    location_address=edit_loc,
                )
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        st.markdown("---")
        # Admin Archive Complaint
        st.markdown("### Archive Complaint")
        st.caption(
            "Archiving hides this complaint from normal views while preserving "
            "the full record and audit history. A reason is required."
        )
        with st.form(f"archive_form_{selected_id}", clear_on_submit=False):
            archive_reason = st.text_input(
                "Archive Reason",
                placeholder="Why is this complaint being archived?",
                key=f"admin_archive_reason_{selected_id}",
            )
            archive_submit = st.form_submit_button(
                "Archive Complaint", use_container_width=True
            )
            if archive_submit:
                if not archive_reason.strip():
                    st.error("An archive reason is required.")
                else:
                    ok, msg = archive_complaint(
                        complaint_id=selected_id,
                        admin_id=user["id"],
                        reason=archive_reason,
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        st.markdown("#### Audit History")
        history_records = get_complaint_history(selected_id)
        for h in history_records:
            old_label = h["old_status"] if h["old_status"] else "Submission"
            st.markdown(
                f"""
                <div style="border-left:3px solid #BFDBFE;padding-left:0.75rem;margin-bottom:0.75rem;">
                    <strong>{old_label} &rarr; {h['new_status']}</strong>
                    <span style="color:#64748B;font-size:0.85rem;">({h['changed_at'][:16]})</span><br/>
                    <span style="color:#1E293B;font-size:0.85rem;">By {h['changed_by_name']} ({h['changed_by_role'].capitalize()})</span><br/>
                    <em style="color:#1E293B;font-size:0.85rem;">"{h['remarks'] or 'No remarks'}"</em>
                </div>
                """,
                unsafe_allow_html=True,
            )
# ---------------------------------------------------------
# View: Admin - AI Duplicate Detection Review
# ---------------------------------------------------------
def render_admin_duplicate_review(user: dict):
    """Inspection and review interface for potential duplicate complaint pairs.
    Features:
    - Separate tabs for Pending, Confirmed, Not Duplicate, All
    - Search by complaint ID, category, location
    - Sort by similarity score
    - Pagination (15 records per page)
    - Side-by-side complaint comparison
    - Confirm Duplicate / Mark Not Duplicate actions
    """
    page_header(
        "Duplicate Reports",
        "Review suspected duplicate complaints detected by AI similarity analysis.",
    )
    # Get counts
    from modules.ai.duplicates import get_duplicate_counts
    counts = get_duplicate_counts()
    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card("Total Candidates", str(counts["All"]))
    with k2:
        kpi_card("Pending Review", str(counts["Pending Review"]))
    with k3:
        kpi_card("Confirmed", str(counts["Confirmed Duplicate"]))
    with k4:
        kpi_card("Not Duplicate", str(counts["Marked Not Duplicate"]))
    section_divider()
    # Tabs for status filtering
    tab_pending, tab_confirmed, tab_not_dup, tab_all = st.tabs(
        ["Pending Review", "Confirmed", "Not Duplicate", "All"]
    )
    status_map = {
        "Pending Review": "Pending Review",
        "Confirmed": "Confirmed Duplicate",
        "Not Duplicate": "Marked Not Duplicate",
        "All": "All",
    }
    for tab, tab_name in zip(
        [tab_pending, tab_confirmed, tab_not_dup, tab_all],
        ["Pending Review", "Confirmed", "Not Duplicate", "All"],
    ):
        with tab:
            status_filter = status_map[tab_name]
            # Search and sort controls
            col_search, col_sort = st.columns([2, 1])
            with col_search:
                search_kw = st.text_input(
                    "Search",
                    placeholder="Complaint ID, category, or location...",
                    key=f"dup_search_{tab_name}",
                )
            with col_sort:
                sort_option = st.selectbox(
                    "Sort by",
                    ["Similarity (High to Low)", "Similarity (Low to High)", "Newest", "Oldest"],
                    key=f"dup_sort_{tab_name}",
                )
            sort_map = {
                "Similarity (High to Low)": "similarity_desc",
                "Similarity (Low to High)": "similarity_asc",
                "Newest": "newest",
                "Oldest": "oldest",
            }
            sort_by = sort_map[sort_option]
            # Pagination state
            page_key = f"dup_page_{tab_name}"
            if page_key not in st.session_state:
                st.session_state[page_key] = 1
            page_size = 15
            matches, total_count = get_all_duplicate_matches(
                status_filter=status_filter,
                search_query=search_kw,
                sort_by=sort_by,
                page=st.session_state[page_key],
                page_size=page_size,
            )
            total_pages = max(1, (total_count + page_size - 1) // page_size)
            if not matches:
                empty_state("📭", "No duplicate candidates", "No matches found for this filter.")
                continue
            st.markdown(f"**Showing {len(matches)} of {total_count} candidate(s)**")
            for m in matches:
                match_id = m["match_id"]
                score = m["similarity_score"]
                status = m["status"]
                score_color = "#1E40AF" if score >= 75.0 else ("#3B82F6" if score >= 60.0 else "#64748B")
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background-color:#FFFFFF;border:1px solid #E2E8F0;border-radius:8px;padding:1rem;margin-bottom:1rem;">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">
                                <span style="font-size:1.1rem;font-weight:700;color:#1E293B;">Pair #{match_id}</span>
                                <div>
                                    <span style="background-color:{score_color};color:#FFFFFF;padding:0.2rem 0.6rem;border-radius:9999px;font-weight:700;font-size:0.85rem;">
                                        {score}% Similarity
                                    </span>
                                    <span style="margin-left:0.5rem;font-weight:600;color:#1E293B;">
                                        {status}
                                    </span>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"#### Ticket #{m['original_complaint_id']}")
                        st.markdown(f"**Title:** {m['orig_title']}")
                        st.markdown(f"**Category:** `{m['orig_category']}` | **Status:** {m['orig_status']}")
                        st.markdown(f"**Location:** {m['orig_address']}")
                        st.caption(f"Submitted: {m['orig_created_at'][:16]}")
                    with col_b:
                        st.markdown(f"#### Ticket #{m['duplicate_complaint_id']}")
                        st.markdown(f"**Title:** {m['dup_title']}")
                        st.markdown(f"**Category:** `{m['dup_category']}` | **Status:** {m['dup_status']}")
                        st.markdown(f"**Location:** {m['dup_address']}")
                        st.caption(f"Submitted: {m['dup_created_at'][:16]}")
                    # Similarity breakdown
                    with st.expander("Similarity Breakdown", expanded=False):
                        st.markdown(f"**Text Similarity:** {m.get('text_similarity_pct', 'N/A')}%")
                        st.markdown(f"**Category Match:** {'Yes' if m.get('orig_category') == m.get('dup_category') else 'No'}")
                        if m.get("distance_meters") is not None:
                            st.markdown(f"**Distance:** {m['distance_meters']} meters")
                        else:
                            st.markdown("**Distance:** N/A (no GPS coordinates)")
                    if status == "Pending Review":
                        st.markdown("---")
                        col_btn1, col_btn2, col_rem = st.columns([1, 1, 2])
                        with col_rem:
                            remarks_input = st.text_input(
                                "Review Note",
                                placeholder="e.g., Verified identical pothole report",
                                key=f"rem_{match_id}_{tab_name}_{st.session_state[page_key]}",
                            )
                        with col_btn1:
                            if st.button("Confirm Duplicate", key=f"conf_{match_id}_{tab_name}_{st.session_state[page_key]}", type="primary", use_container_width=True):
                                ok, msg = review_duplicate_match(
                                    match_id=match_id,
                                    admin_id=user["id"],
                                    decision="Confirmed Duplicate",
                                    remarks=remarks_input,
                                )
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        with col_btn2:
                            if st.button("Mark Not Duplicate", key=f"not_{match_id}_{tab_name}_{st.session_state[page_key]}", use_container_width=True):
                                ok, msg = review_duplicate_match(
                                    match_id=match_id,
                                    admin_id=user["id"],
                                    decision="Marked Not Duplicate",
                                    remarks=remarks_input,
                                )
                                if ok:
                                    st.info(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                    else:
                        st.caption(f"Reviewed by: {m.get('reviewer_name', 'Admin')} on {m.get('reviewed_at', 'N/A')[:16]}")
                    st.markdown("---")
            # Pagination controls
            if total_pages > 1:
                col_prev, col_info, col_next = st.columns([1, 2, 1])
                with col_prev:
                    if st.button("Previous", key=f"dup_prev_{tab_name}", disabled=(st.session_state[page_key] <= 1)):
                        st.session_state[page_key] = max(1, st.session_state[page_key] - 1)
                        st.rerun()
                with col_info:
                    st.markdown(f"Page {st.session_state[page_key]} of {total_pages}")
                with col_next:
                    if st.button("Next", key=f"dup_next_{tab_name}", disabled=(st.session_state[page_key] >= total_pages)):
                        st.session_state[page_key] = min(total_pages, st.session_state[page_key] + 1)
                        st.rerun()
def render_admin_analytics(user: dict):
    """Interactive Plotly analytics dashboard for municipal administrators."""
    page_header(
        "Civic Analytics",
        "City-wide performance indicators, resolution timelines, and issue distribution.",
    )
    data = get_admin_analytics_data()
    # KPI cards
    k1, k2, k3 = st.columns(3)
    with k1:
        kpi_card("Total Complaints", str(data["total_complaints"]))
    with k2:
        kpi_card("Pending", str(data["pending_count"]))
    with k3:
        kpi_card("In Progress", str(data["in_progress_count"]))
    k4, k5, k6 = st.columns(3)
    with k4:
        kpi_card("Resolved", str(data["resolved_count"]))
    with k5:
        kpi_card("Resolution Rate", f"{data['resolution_rate']}%")
    with k6:
        kpi_card("Duplicate Reports", str(data["total_duplicate_flags"]))
    section_divider()
    if data["total_complaints"] == 0:
        empty_state("📭", "No data available", "No complaint data available yet to generate analytics.")
        return
    # Charts row 1: Status donut + Category bar
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        fig_status = build_status_donut_chart(data["status_distribution"], title="Status Distribution")
        st.plotly_chart(fig_status, use_container_width=True)
    with col_c2:
        fig_cat = build_category_bar_chart(data["category_distribution"], title="Complaints by Category")
        st.plotly_chart(fig_cat, use_container_width=True)
    section_divider()
    # Charts row 2: Monthly trends + Resolved vs Received
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if data["monthly_trend"]:
            fig_trend = build_monthly_trend_chart(data["monthly_trend"], title="Monthly Complaint Inflow")
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.caption("Monthly trend data not yet populated.")
    with col_t2:
        if data["monthly_resolved_vs_received"]:
            fig_rv = build_monthly_resolved_vs_received_chart(
                data["monthly_resolved_vs_received"], title="Resolved vs Received"
            )
            st.plotly_chart(fig_rv, use_container_width=True)
        else:
            st.caption("Resolution data not yet populated.")
    section_divider()
    # AI Confidence distribution (if data exists)
    if data["ai_confidence_distribution"]:
        st.subheader("AI Confidence Distribution")
        conf_df = {r["confidence_band"]: r["count"] for r in data["ai_confidence_distribution"]}
        for band, count in conf_df.items():
            st.markdown(f"- **{band}**: {count} complaints")
    section_divider()
    # Top locations
    if data["top_locations"]:
        st.subheader("Top Reported Locations")
        for loc in data["top_locations"][:5]:
            pct = round((loc["count"] / data["total_complaints"]) * 100.0, 1)
            st.markdown(
                f"""
                <div style="background-color:#FFFFFF;border:1px solid #E2E8F0;padding:0.6rem 0.8rem;border-radius:6px;margin-bottom:0.4rem;display:flex;justify-content:space-between;">
                    <span><strong>{loc['location_address'][:60]}</strong></span>
                    <span>{loc['count']} issues ({pct}%)</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    section_divider()
    # Recent complaints table
    if data["recent_complaints"]:
        st.subheader("Recent Complaints")
        for c in data["recent_complaints"]:
            st.markdown(
                f"""
                <div style="background-color:#FFFFFF;border:1px solid #E2E8F0;padding:0.6rem 0.8rem;border-radius:6px;margin-bottom:0.4rem;display:flex;justify-content:space-between;">
                    <span><strong>#{c['id']} {c['title'][:40]}</strong> - {c['category']} - {c['status']}</span>
                    <span style="color:#64748B;font-size:0.85rem;">{c['created_at'][:16]}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
# ---------------------------------------------------------
# View: Admin - Audit Trail & Logs
# ---------------------------------------------------------
def render_admin_audit_logs(user: dict):
    """Displays comprehensive administrative actions audit log."""
    page_header(
        "Audit Trail",
        "Complete chronological record of all administrative decisions, status overrides, and updates.",
    )
    logs = get_admin_audit_logs(limit=100)
    if not logs:
        empty_state(
            "📭",
            "No audit events",
            "No administrative actions have been logged yet.",
        )
        return
    st.markdown(f"**Total Logged Events: {len(logs)}**")
    for l in logs:
        complaint_tag = f"Ticket #{l['complaint_id']}" if l["complaint_id"] else "General System Action"
        st.markdown(
                f"""
                <div class="complaint-card" style="padding: 0.9rem; margin-bottom: 0.6rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>{complaint_tag} - {l['action_type']}</strong>
                        <span style="color: #64748B; font-size: 0.85rem;">{l['action_timestamp']}</span>
                    </div>
                    <div style="color: #1E40AF; font-size: 0.88rem; margin: 0.25rem 0;">
                        Admin: <strong>{l['admin_name']}</strong> ({l['admin_email']})
                    </div>
                    <div style="color: #1E293B; font-size: 0.9rem;">
                        {l['action_details']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
# ---------------------------------------------------------
# Sidebar Component (Authenticated Users)
# ---------------------------------------------------------
def render_sidebar(user: dict):
    """Displays user profile, navigation controls, and logout button."""
    with st.sidebar:
        st.markdown('<div class="sidebar-brand">Civic Portal</div>', unsafe_allow_html=True)
        st.markdown('---')
        st.markdown(f'<div class="sidebar-user-name">{user["full_name"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sidebar-user-email secondary-text">{user["email"]}</div>', unsafe_allow_html=True)
        if user.get("role") == "admin":
            st.markdown(
                '<span style="background-color:#DBEAFE;color:#1E40AF;font-weight:700;padding:0.25rem 0.75rem;border-radius:9999px;font-size:0.8rem;border:1px solid #BFDBFE;">Administrator</span>',
                unsafe_allow_html=True,
            )
            st.markdown('---')
            st.markdown('<div class="sidebar-section-label">Navigation</div>', unsafe_allow_html=True)
            stored_admin_page = st.session_state.get("_admin_nav_page")
            safe_admin_page = normalize_nav_choice(stored_admin_page, ADMIN_NAV_OPTIONS)
            st.session_state["_admin_nav_page"] = safe_admin_page
            admin_index = ADMIN_NAV_OPTIONS.index(safe_admin_page)
            nav_choice = st.radio(
                "Admin Navigation",
                options=ADMIN_NAV_OPTIONS,
                index=admin_index,
                label_visibility="collapsed",
                key="admin_nav_radio",
            )
            st.session_state["_admin_nav_page"] = nav_choice
        else:
            st.markdown(
                '<span style="background-color:#EFF6FF;color:#1E40AF;font-weight:700;padding:0.25rem 0.75rem;border-radius:9999px;font-size:0.8rem;border:1px solid #BFDBFE;">Citizen</span>',
                unsafe_allow_html=True,
            )
            st.markdown('---')
            st.markdown('<div class="sidebar-section-label">Navigation</div>', unsafe_allow_html=True)
            stored_citizen_page = st.session_state.get("_citizen_nav_page")
            safe_citizen_page = normalize_nav_choice(stored_citizen_page, CITIZEN_NAV_OPTIONS)
            st.session_state["_citizen_nav_page"] = safe_citizen_page
            citizen_index = CITIZEN_NAV_OPTIONS.index(safe_citizen_page)
            nav_choice = st.radio(
                "Citizen Navigation",
                options=CITIZEN_NAV_OPTIONS,
                index=citizen_index,
                label_visibility="collapsed",
                key="citizen_nav_radio",
            )
            st.session_state["_citizen_nav_page"] = nav_choice
        st.markdown('')
        st.markdown(f'<div class="secondary-text" style="font-size:0.8rem;">Joined: {user.get("created_at", "N/A")[:10]}</div>', unsafe_allow_html=True)
        st.markdown('---')
        if st.button("Log Out", use_container_width=True):
            logout_user()
            st.session_state.pop("_citizen_nav_page", None)
            st.session_state.pop("_admin_nav_page", None)
            st.rerun()
        return nav_choice
# ---------------------------------------------------------
# Main Application Entry Point
# ---------------------------------------------------------
def main():
    initialize_app()
    if is_authenticated():
        current_user = get_current_user()
        if not current_user:
            logout_user()
            st.rerun()
            return
        nav_choice = render_sidebar(current_user)
        if is_admin():
            if nav_choice == "📊 Dashboard":
                render_admin_dashboard(current_user)
            elif nav_choice == "🗂️ All Complaints":
                render_admin_complaint_management(current_user)
            elif nav_choice == "🔁 Duplicate Reports":
                render_admin_duplicate_review(current_user)
            elif nav_choice == "🗺️ Map View":
                render_admin_complaint_map(current_user)
            elif nav_choice == "📈 Analytics":
                render_admin_analytics(current_user)
            elif nav_choice == "🧾 Admin Activity":
                render_admin_audit_logs(current_user)
        else:
            if nav_choice == "🏠 Overview":
                render_citizen_dashboard(current_user)
            elif nav_choice == "📝 Report an Issue":
                render_citizen_report_issue(current_user)
            elif nav_choice == "📄 My Reports":
                render_citizen_my_complaints(current_user)
            elif nav_choice == "📍 Track Complaints":
                render_citizen_complaint_map(current_user)
            elif nav_choice == "📊 My Activity":
                render_citizen_analytics(current_user)
            elif nav_choice == "👤 Profile":
                render_citizen_profile(current_user)
    else:
        render_auth_view()
    portal_footer(show_navigation=is_authenticated())
if __name__ == "__main__":
    main()
