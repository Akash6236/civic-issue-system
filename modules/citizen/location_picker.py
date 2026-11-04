"""
Location Picker Module
AI-Powered Civic Issue Reporting and Management System

Interactive location selection for civic complaint submission.

Supports multiple input methods:
1. Search by address/landmark (OpenStreetMap Nominatim geocoding)
2. Browser Geolocation API (GPS) - user-triggered only
3. Select directly on Folium map (click + drag)
4. Paste Google Maps / OpenStreetMap link

Privacy:
- Location data is only collected when the user explicitly provides it.
- GPS permission is never requested without a user action (button click).
- Coordinates are never mandatory; users can submit without location data.
- No API keys are used; Nominatim is called per OpenStreetMap usage policy.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium

# Nominatim configuration (OpenStreetMap geocoding, free, no API key).
NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_USER_AGENT = "CivicIssueReportingSystem/1.0 (municipal-civic-app)"

# Regex patterns for extracting coordinates from map links.
GOOGLE_MAPS_PATTERNS = [
    r"@([-+]?\d+\.?\d*),([-+]?\d+\.?\d*),",
    r"\/@([-+]?\d+\.?\d*),([-+]?\d+\.?\d*),",
    r"\?ll=([-+]?\d+\.?\d*),([-+]?\d+\.?\d*)",
    r"!3d([-+]?\d+\.?\d*)!4d([-+]?\d+\.?\d*)",
]

OSM_PATTERNS = [
    r"#map=(\d+)/([-+]?\d+\.?\d*)/([-+]?\d+\.?\d*)",
    r"mlat=([-+]?\d+\.?\d*)&?mlon=([-+]?\d+\.?\d*)",
]


def _validate_coords(lat: float, lon: float) -> bool:
    """Check that latitude and longitude are within valid ranges."""
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


def _parse_map_link(link: str) -> Optional[Tuple[float, float]]:
    """
    Extract latitude and longitude from a Google Maps or OpenStreetMap URL.

    Supports common URL patterns but does not claim to support every format.
    Returns None if no coordinates can be extracted.
    """
    if not link or not link.strip():
        return None

    link = link.strip()

    # Google Maps patterns
    for pattern in GOOGLE_MAPS_PATTERNS:
        match = re.search(pattern, link)
        if match:
            try:
                lat = float(match.group(1))
                lon = float(match.group(2))
                if _validate_coords(lat, lon):
                    return lat, lon
            except (ValueError, IndexError):
                continue

    # OpenStreetMap patterns
    for pattern in OSM_PATTERNS:
        match = re.search(pattern, link)
        if match:
            try:
                if pattern.startswith(r"#map="):
                    # #map=zoom/lat/lon
                    lat = float(match.group(2))
                    lon = float(match.group(3))
                else:
                    # mlat=...&mlon=...
                    lat = float(match.group(1))
                    lon = float(match.group(2))
                if _validate_coords(lat, lon):
                    return lat, lon
            except (ValueError, IndexError):
                continue

    return None


def _geocode_address(query: str) -> List[Dict[str, Any]]:
    """
    Query OpenStreetMap Nominatim for address suggestions.

    Returns a list of dicts with keys: lat, lon, display_name, type.
    Respects Nominatim usage policy (one request, proper User-Agent).
    Returns an empty list on network errors or no results.
    """
    if not query or not query.strip():
        return []

    try:
        headers = {"User-Agent": NOMINATIM_USER_AGENT}
        params = {
            "q": query.strip(),
            "format": "json",
            "limit": 5,
            "addressdetails": 1,
        }
        response = requests.get(
            NOMINATIM_SEARCH_URL,
            params=params,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        results = response.json()

        suggestions = []
        for r in results:
            try:
                lat = float(r["lat"])
                lon = float(r["lon"])
                if _validate_coords(lat, lon):
                    suggestions.append({
                        "lat": lat,
                        "lon": lon,
                        "display_name": r.get("display_name", query),
                        "type": r.get("type", ""),
                    })
            except (KeyError, ValueError, TypeError):
                continue

        return suggestions

    except Exception:
        return []


def _reverse_geocode(lat: float, lon: float) -> Optional[str]:
    """
    Reverse-geocode coordinates to a human-readable address using Nominatim.

    Returns the display name or None on failure.
    """
    if not _validate_coords(lat, lon):
        return None

    try:
        headers = {"User-Agent": NOMINATIM_USER_AGENT}
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "zoom": 18,
            "addressdetails": 1,
        }
        response = requests.get(
            NOMINATIM_REVERSE_URL,
            params=params,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()
        return result.get("display_name")
    except Exception:
        return None


def _render_gps_button() -> Optional[Tuple[float, float]]:
    """
    Render a 'Use My Current Location' button using the browser Geolocation API.

    Permission is only requested when the user clicks the button (never
    automatically). Returns detected coordinates or None.
    """
    st.markdown("#### 📍 Use My Current Location")
    st.info(
        "Click the button below to allow your browser to detect your location. "
        "You will be asked to grant location permission. This is optional and "
        "you can deny the request."
    )

    gps_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Geolocation</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 10px; }
            button {
                background-color: #34483D;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }
            button:disabled { background-color: #9CA3AF; cursor: not-allowed; }
            #status { margin-top: 10px; font-size: 13px; }
            .success { color: #22543D; }
            .error { color: #C53030; }
            .coords { margin-top: 8px; font-family: monospace; }
        </style>
    </head>
    <body>
        <button id="gpsBtn">Use My Current Location</button>
        <div id="status"></div>
        <div id="coords" class="coords"></div>

        <script>
            const btn = document.getElementById('gpsBtn');
            const status = document.getElementById('status');
            const coords = document.getElementById('coords');

            btn.addEventListener('click', async () => {
                if (!navigator.geolocation) {
                    status.innerHTML = '<span class="error">Geolocation is not supported by your browser.</span>';
                    btn.disabled = true;
                    return;
                }

                btn.disabled = true;
                btn.textContent = 'Detecting location...';
                status.innerHTML = '';
                coords.innerHTML = '';

                try {
                    const position = await new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(resolve, reject, {
                            enableHighAccuracy: true,
                            timeout: 10000,
                            maximumAge: 0,
                        });
                    });

                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    const acc = position.coords.accuracy;

                    status.innerHTML = '<span class="success">Location detected.</span>';
                    coords.innerHTML = 'Latitude: ' + lat.toFixed(6) + '<br>Longitude: ' + lon.toFixed(6) + '<br>Accuracy: ~' + Math.round(acc) + 'm';
                    coords.innerHTML += '<br><small>Enter these coordinates below to use this location.</small>';
                } catch (err) {
                    let msg = 'Unable to detect location.';
                    if (err.code === 1) msg = 'Location access was denied by the user.';
                    else if (err.code === 2) msg = 'Location information is unavailable.';
                    else if (err.code === 3) msg = 'Location request timed out.';
                    status.innerHTML = '<span class="error">' + msg + '</span>';
                    btn.disabled = false;
                    btn.textContent = 'Use My Current Location';
                }
            });
        </script>
    </body>
    </html>
    """

    st.components.v1.html(gps_html, height=150)

    # Manual coordinate entry fields (enabled, so user can type detected values)
    col1, col2 = st.columns(2)
    with col1:
        gps_lat = st.number_input(
            "Latitude",
            min_value=-90.0,
            max_value=90.0,
            value=None,
            format="%.6f",
            key="gps_lat_input",
            help="Enter the latitude detected by browser geolocation.",
        )
    with col2:
        gps_lon = st.number_input(
            "Longitude",
            min_value=-180.0,
            max_value=180.0,
            value=None,
            format="%.6f",
            key="gps_lon_input",
            help="Enter the longitude detected by browser geolocation.",
        )

    if gps_lat is not None and gps_lon is not None:
        if st.button("Apply Detected Location", key="gps_apply_btn", use_container_width=True, type="primary"):
            return gps_lat, gps_lon

    return None


def _render_address_search() -> Optional[Tuple[float, float, str]]:
    """
    Render an address search field using OpenStreetMap Nominatim.

    Returns (lat, lon, display_name) or None.
    """
    st.markdown("#### 🔍 Search Area, Street or Landmark")
    st.caption(
        "Examples: Yelahanka New Town, Bengaluru | NMIT, Bengaluru | Hebbal Flyover, Bengaluru"
    )

    search_query = st.text_input(
        "Search location",
        placeholder="Enter area, street, or landmark...",
        key="address_search_input",
    )

    # Persist search suggestions across Streamlit reruns.
    suggestions_key = "address_search_suggestions"
    if st.button("Search", key="address_search_btn", use_container_width=True):
        if search_query and search_query.strip():
            with st.spinner("Searching..."):
                st.session_state[suggestions_key] = _geocode_address(search_query)
        else:
            st.session_state[suggestions_key] = []

    suggestions = st.session_state.get(suggestions_key, [])

    if suggestions:
        st.caption(f"Found {len(suggestions)} result(s):")
        options = {}
        for s in suggestions:
            label = f"{s['display_name']} ({s['type']})" if s["type"] else s["display_name"]
            options[label] = (s["lat"], s["lon"], s["display_name"])

        selected_label = st.selectbox(
            "Select a location:",
            options=list(options.keys()),
            key="address_search_result",
        )
        if selected_label:
            lat, lon, display_name = options[selected_label]
            return lat, lon, display_name

    return None


def _render_map_link() -> Optional[Tuple[float, float]]:
    """
    Render a field to paste a Google Maps or OpenStreetMap link.

    Returns (lat, lon) or None.
    """
    st.markdown("#### 🔗 Paste a Map Link")
    st.caption(
        "Paste a Google Maps or OpenStreetMap link to extract coordinates. "
        "Unsupported formats can be ignored; use map selection instead."
    )

    link = st.text_input(
        "Map link",
        placeholder="https://www.google.com/maps/@12.9716,77.5946,15z",
        key="map_link_input",
    )

    # Persist extracted coordinates across Streamlit reruns.
    extracted_key = "map_link_extracted"
    if link and link.strip():
        if st.button("Extract Coordinates", key="map_link_extract_btn", use_container_width=True):
            result = _parse_map_link(link)
            if result:
                st.session_state[extracted_key] = result
                st.success(f"Coordinates extracted: {result[0]:.6f}, {result[1]:.6f}")
            else:
                st.session_state.pop(extracted_key, None)
                st.error(
                    "Could not extract coordinates from this link. "
                    "Please try a different link or use map selection."
                )

    extracted = st.session_state.get(extracted_key)
    if extracted:
        return extracted

    return None


def _render_selection_map(
    lat: Optional[float],
    lon: Optional[float],
    key_suffix: str = "",
) -> Optional[Tuple[float, float]]:
    """
    Render a Folium map where the user can click to select a location.

    Returns clicked coordinates or None.
    """
    st.markdown("#### 🗺️ Select on Map")

    center = [lat, lon] if lat is not None and lon is not None else [20.5937, 78.9629]
    zoom = 15 if lat is not None and lon is not None else 5

    m = folium.Map(location=center, zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="&copy; OpenStreetMap contributors",
        name="OpenStreetMap",
        max_zoom=19,
    ).add_to(m)

    if lat is not None and lon is not None:
        folium.Marker(
            location=[lat, lon],
            tooltip="Selected location",
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(m)

    # Use returned_objects to capture map clicks
    map_data = st_folium(
        m,
        width=700,
        height=400,
        returned_objects=["last_clicked"],
        key=f"location_map_{key_suffix}",
    )

    if map_data and map_data.get("last_clicked"):
        clicked = map_data["last_clicked"]
        if clicked and isinstance(clicked, dict):
            clicked_lat = clicked.get("lat")
            clicked_lon = clicked.get("lng")
            if clicked_lat is not None and clicked_lon is not None:
                return clicked_lat, clicked_lon

    return None


def render_location_picker(
    default_lat: Optional[float] = None,
    default_lon: Optional[float] = None,
    default_address: str = "",
) -> Dict[str, Any]:
    """
    Render an interactive location picker with multiple input methods.

    The user can select a location via:
    1. Address/landmark search (Nominatim geocoding)
    2. Browser geolocation (GPS) - user-triggered only
    3. Click on map
    4. Paste map link

    Args:
        default_lat: Default latitude (optional).
        default_lon: Default longitude (optional).
        default_address: Default location address text (optional).

    Returns:
        dict with keys:
            - latitude: Optional[float]
            - longitude: Optional[float]
            - location_address: str
            - location_source: str ('GPS', 'Manual', or None)
            - location_confirmed: bool
            - submitted: bool (True if user clicked 'Use This Location')
    """
    # Initialize session state for location picker
    state_prefix = "loc_picker_"
    if f"{state_prefix}lat" not in st.session_state:
        st.session_state[f"{state_prefix}lat"] = default_lat
    if f"{state_prefix}lon" not in st.session_state:
        st.session_state[f"{state_prefix}lon"] = default_lon
    if f"{state_prefix}address" not in st.session_state:
        st.session_state[f"{state_prefix}address"] = default_address
    if f"{state_prefix}source" not in st.session_state:
        st.session_state[f"{state_prefix}source"] = None
    if f"{state_prefix}confirmed" not in st.session_state:
        st.session_state[f"{state_prefix}confirmed"] = False

    result: Dict[str, Any] = {
        "latitude": None,
        "longitude": None,
        "location_address": "",
        "location_source": None,
        "location_confirmed": False,
        "submitted": False,
    }

    st.markdown("### 📍 Select Complaint Location")
    st.caption(
        "Choose how to specify the location of this civic issue. "
        "Location is optional - you can submit without coordinates."
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["🔍 Search Address", "📍 Use My Location", "🗺️ Select on Map", "🔗 Map Link"]
    )

    with tab1:
        search_result = _render_address_search()
        if search_result:
            lat, lon, display_name = search_result
            st.session_state[f"{state_prefix}lat"] = lat
            st.session_state[f"{state_prefix}lon"] = lon
            st.session_state[f"{state_prefix}address"] = display_name
            st.session_state[f"{state_prefix}source"] = "Manual"
            st.session_state[f"{state_prefix}confirmed"] = False

    with tab2:
        gps_result = _render_gps_button()
        if gps_result:
            lat, lon = gps_result
            # Reverse-geocode to get human-readable address
            with st.spinner("Resolving address..."):
                address = _reverse_geocode(lat, lon)
            st.session_state[f"{state_prefix}lat"] = lat
            st.session_state[f"{state_prefix}lon"] = lon
            st.session_state[f"{state_prefix}address"] = address or f"{lat:.6f}, {lon:.6f}"
            st.session_state[f"{state_prefix}source"] = "GPS"
            st.session_state[f"{state_prefix}confirmed"] = False

    with tab3:
        current_lat = st.session_state.get(f"{state_prefix}lat")
        current_lon = st.session_state.get(f"{state_prefix}lon")
        map_result = _render_selection_map(current_lat, current_lon)
        if map_result:
            lat, lon = map_result
            st.session_state[f"{state_prefix}lat"] = lat
            st.session_state[f"{state_prefix}lon"] = lon
            st.session_state[f"{state_prefix}address"] = f"{lat:.6f}, {lon:.6f}"
            st.session_state[f"{state_prefix}source"] = "Manual"
            st.session_state[f"{state_prefix}confirmed"] = False

    with tab4:
        link_result = _render_map_link()
        if link_result:
            lat, lon = link_result
            st.session_state[f"{state_prefix}lat"] = lat
            st.session_state[f"{state_prefix}lon"] = lon
            st.session_state[f"{state_prefix}address"] = f"{lat:.6f}, {lon:.6f}"
            st.session_state[f"{state_prefix}source"] = "Manual"
            st.session_state[f"{state_prefix}confirmed"] = False

    # Address override (manual text)
    st.markdown("#### 📝 Location Address / Landmark")
    address_input = st.text_input(
        "Address description",
        value=st.session_state.get(f"{state_prefix}address", default_address),
        key=f"{state_prefix}address_input",
        placeholder="e.g., Near City Hospital Gate 2, MG Road",
        help="Describe the location in plain text.",
    )
    st.session_state[f"{state_prefix}address"] = address_input

    # Coordinate confirmation (display only, not manual entry)
    current_lat = st.session_state.get(f"{state_prefix}lat")
    current_lon = st.session_state.get(f"{state_prefix}lon")
    if current_lat is not None and current_lon is not None:
        source = st.session_state.get(f"{state_prefix}source", None)
        source_label = source if source else "Manual"

        st.markdown(
            f"""
            <div style="background-color:#F6F0E3;border:1px solid #D8D6CF;border-radius:8px;padding:1rem;margin:1rem 0;">
                <h4 style="margin:0 0 0.5rem 0;color:#34483D;font-size:1rem;">Selected Location</h4>
                <p style="margin:0;color:#343A36;font-size:0.9rem;"><strong>Address:</strong> {address_input or f"{current_lat:.6f}, {current_lon:.6f}"}</p>
                <p style="margin:0;color:#747A74;font-size:0.85rem;"><strong>Source:</strong> {source_label}</p>
                <p style="margin:0;color:#747A74;font-size:0.85rem;"><strong>Coordinates:</strong> ({current_lat:.6f}, {current_lon:.6f})</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Confirm button
        if st.button("✅ Use This Location", type="primary", use_container_width=True, key=f"{state_prefix}confirm_btn"):
            st.session_state[f"{state_prefix}confirmed"] = True
            result["latitude"] = current_lat
            result["longitude"] = current_lon
            result["location_address"] = address_input or f"{current_lat:.6f}, {current_lon:.6f}"
            result["location_source"] = st.session_state.get(f"{state_prefix}source", None)
            result["location_confirmed"] = True
            result["submitted"] = True
    else:
        st.info(
            "No location selected yet. Use one of the methods above to choose "
            "a location, or leave blank to submit without coordinates."
        )

    # If previously confirmed, populate result
    if st.session_state.get(f"{state_prefix}confirmed", False):
        result["latitude"] = st.session_state.get(f"{state_prefix}lat")
        result["longitude"] = st.session_state.get(f"{state_prefix}lon")
        result["location_address"] = st.session_state.get(f"{state_prefix}address", "")
        result["location_source"] = st.session_state.get(f"{state_prefix}source", None)
        result["location_confirmed"] = True
        result["submitted"] = True

    return result
