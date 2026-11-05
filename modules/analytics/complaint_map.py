"""
Complaint Map Module
AI-Powered Civic Issue Reporting and Management System

Interactive Folium/OpenStreetMap visualization of civic complaints.

Privacy design:
- Complaints without latitude/longitude are never shown (no invented coordinates).
- Displayed coordinates are deterministically jittered (~50 m) so exact
  residential locations are not exposed.
- Map popups never include citizen name, email, or phone number.
"""

import random
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

import streamlit as st

from modules.admin.complaints import VALID_STATUSES
from modules.citizen.complaints import CATEGORIES
from modules.database import get_connection
from modules.ui.theme import page_header

# Fallback map centre (geographic centre of India) used when no complaints
# have usable coordinates.
DEFAULT_CENTER = [20.5937, 78.9629]
DEFAULT_ZOOM = 6

# OpenStreetMap tile configuration (public, no API key required).
OSM_TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
OSM_ATTRIBUTION = (
    "&copy; <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a> "
    "contributors"
)

# Category -> Folium icon colour. Colours are purely visual; no personal data.
CATEGORY_COLORS = {
    "Garbage": "green",
    "Road Damage": "orange",
    "Water Leakage": "blue",
    "Streetlight": "purple",
    "Drainage": "lightblue",
    "Public Sanitation": "darkred",
    "Other": "gray",
}

# Small deterministic jitter (~50 m) to obscure exact residential coordinates.
JITTER_DEGREES = 0.0005


def _jitter(lat: float, lon: float, complaint_id: int) -> Tuple[float, float]:
    """Return a deterministic, slightly offset coordinate for privacy."""
    rng = random.Random(complaint_id)
    jitter_lat = lat + rng.uniform(-JITTER_DEGREES, JITTER_DEGREES)
    jitter_lon = lon + rng.uniform(-JITTER_DEGREES, JITTER_DEGREES)
    return jitter_lat, jitter_lon


def _category_color(category: str) -> str:
    """Return a Folium icon colour for a complaint category."""
    return CATEGORY_COLORS.get(category, "gray")


def get_map_complaints(
    user_id: Optional[int] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch complaints that have usable coordinates, optionally filtered.

    Only complaints with both latitude and longitude are returned. Complaints
    without location data are never invented or shown on the map.

    Privacy: the returned rows never include citizen name, email, or phone.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT id, title, category, status, location_address,
                       latitude, longitude, created_at
                FROM complaints
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """
            params: List[Any] = []

            if user_id is not None:
                query += " AND user_id = ?"
                params.append(user_id)

            if category and category != "All":
                query += " AND category = ?"
                params.append(category)

            if status and status != "All":
                query += " AND status = ?"
                params.append(status)

            if date_from:
                query += " AND DATE(created_at) >= DATE(?)"
                params.append(date_from.isoformat())

            if date_to:
                query += " AND DATE(created_at) <= DATE(?)"
                params.append(date_to.isoformat())

            query += " ORDER BY created_at DESC;"

            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]

    except Exception:
        return []


def _default_center(complaints: List[Dict[str, Any]]) -> List[float]:
    """Compute map centre from complaint coordinates, with a safe fallback."""
    lats = [c["latitude"] for c in complaints if c.get("latitude") is not None]
    lons = [c["longitude"] for c in complaints if c.get("longitude") is not None]
    if lats and lons:
        return [sum(lats) / len(lats), sum(lons) / len(lons)]
    return list(DEFAULT_CENTER)


def _compute_zoom(complaints: List[Dict[str, Any]]) -> int:
    """
    Compute an appropriate zoom level based on the geographic spread of
    complaints. Returns a zoom that keeps all complaint markers visible
    without being excessively zoomed out.
    """
    lats = [c["latitude"] for c in complaints if c.get("latitude") is not None]
    lons = [c["longitude"] for c in complaints if c.get("longitude") is not None]

    if not lats or not lons:
        return DEFAULT_ZOOM

    lat_spread = max(lats) - min(lats)
    lon_spread = max(lons) - min(lons)
    spread = max(lat_spread, lon_spread)

    # Heuristic: smaller spread -> higher zoom
    if spread < 0.01:
        return 15
    if spread < 0.05:
        return 13
    if spread < 0.1:
        return 11
    if spread < 0.5:
        return 9
    if spread < 2.0:
        return 7
    return DEFAULT_ZOOM


def build_complaint_map(
    complaints: List[Dict[str, Any]],
    center: Optional[List[float]] = None,
    zoom: Optional[int] = None,
) -> folium.Map:
    """
    Build a Folium map with clustered, colour-coded complaint markers.

    Markers show complaint ID, category, status and approximate location only.
    Uses an explicit OpenStreetMap TileLayer with attribution for reliable
    tile loading.
    """
    if center is None:
        center = _default_center(complaints)

    if zoom is None:
        zoom = _compute_zoom(complaints)

    # tiles=None prevents Folium from adding a default tile layer; we add
    # an explicit TileLayer below for reliable OSM tile configuration.
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles=None,
        control_scale=True,
    )

    folium.TileLayer(
        tiles=OSM_TILE_URL,
        attr=OSM_ATTRIBUTION,
        name="OpenStreetMap",
        max_zoom=19,
        min_zoom=0,
        overlay=False,
        control=True,
    ).add_to(m)

    marker_cluster = MarkerCluster(name="Complaints").add_to(m)

    for c in complaints:
        lat = c.get("latitude")
        lon = c.get("longitude")
        if lat is None or lon is None:
            continue

        jitter_lat, jitter_lon = _jitter(lat, lon, int(c["id"]))

        popup_html = (
            f"<b>Ticket #{c['id']}</b><br/>"
            f"Category: {c['category']}<br/>"
            f"Status: {c['status']}<br/>"
            f"Location: {c['location_address'] or 'Not specified'}"
        )

        folium.Marker(
            location=[jitter_lat, jitter_lon],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color=_category_color(c["category"]), icon="info-sign"),
            tooltip=f"Ticket #{c['id']} - {c['category']}",
        ).add_to(marker_cluster)

    return m


def render_admin_complaint_map(user: Dict[str, Any]) -> None:
    """Render the admin city-wide complaint map with filters."""
    page_header(
        "Complaint Map",
        "City-wide visualization of civic complaint locations. "
        "Coordinates are approximate for privacy; citizens' personal details are not shown.",
    )

    with st.form("complaint_map_filters", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            cat_filter = st.selectbox("Category", ["All"] + CATEGORIES)
        with col2:
            status_filter = st.selectbox("Status", ["All"] + VALID_STATUSES)
        with col3:
            date_range = st.date_input("Date Range", value=[])

        st.form_submit_button("Apply Filters", use_container_width=True, type="primary")

    date_from: Optional[date] = None
    date_to: Optional[date] = None
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        date_from, date_to = date_range[0], date_range[1]
    elif isinstance(date_range, date):
        date_from = date_range

    complaints = get_map_complaints(
        category=cat_filter,
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
    )

    if not complaints:
        st.info("No complaints with location data match the selected filters.")
        return

    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    st.caption(f"Showing {len(complaints)} complaint(s) with location data.")

    center = _default_center(complaints)
    zoom = _compute_zoom(complaints)
    m = build_complaint_map(complaints, center=center, zoom=zoom)

    try:
        st_folium(m, width=900, height=600, returned_objects=[])
    except Exception as err:
        st.error(
            "Unable to display the interactive map. This can happen if map tiles "
            "cannot be loaded (e.g., no internet connection or tile service issues). "
            f"Details: {err}"
        )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="map-legend">'
        '<strong>Legend:</strong> '
        '<span style="color:#657A62;">■</span> Garbage · '
        '<span style="color:#C49B59;">■</span> Road Damage · '
        '<span style="color:#8299A0;">■</span> Water Leakage · '
        '<span style="color:#657A62;">■</span> Streetlight · '
        '<span style="color:#8299A0;">■</span> Drainage · '
        '<span style="color:#B87568;">■</span> Public Sanitation · '
        '<span style="color:#6F786F;">■</span> Other'
        '</div>',
        unsafe_allow_html=True,
    )


def render_citizen_complaint_map(user: Dict[str, Any]) -> None:
    """Render a personal map showing only the logged-in citizen's complaints."""
    page_header(
        "My Complaint Map",
        "Your reported civic issues on a map. Only your own complaints are shown.",
    )

    complaints = get_map_complaints(user_id=user["id"])

    if not complaints:
        st.info("You have no complaints with location data to display on a map.")
        return

    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    st.caption(f"Showing {len(complaints)} of your complaint(s) with location data.")

    center = _default_center(complaints)
    zoom = _compute_zoom(complaints)
    m = build_complaint_map(complaints, center=center, zoom=zoom)

    try:
        st_folium(m, width=900, height=600, returned_objects=[])
    except Exception as err:
        st.error(
            "Unable to display the interactive map. This can happen if map tiles "
            "cannot be loaded (e.g., no internet connection or tile service issues). "
            f"Details: {err}"
        )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="map-legend">'
        '<strong>Legend:</strong> '
        '<span style="color:#657A62;">■</span> Garbage · '
        '<span style="color:#C49B59;">■</span> Road Damage · '
        '<span style="color:#8299A0;">■</span> Water Leakage · '
        '<span style="color:#657A62;">■</span> Streetlight · '
        '<span style="color:#8299A0;">■</span> Drainage · '
        '<span style="color:#B87568;">■</span> Public Sanitation · '
        '<span style="color:#6F786F;">■</span> Other'
        '</div>',
        unsafe_allow_html=True,
    )
