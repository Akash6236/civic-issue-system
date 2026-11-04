"""
AI Duplicate Complaint Detection Module
AI-Powered Civic Issue Reporting and Management System

Identifies potential duplicate complaints using text similarity, category matching,
and geographic distance calculations (Haversine formula). Records and manages
reviewable duplicate pairs in compliance with database constraints.
"""

import math
import re
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from modules.database import get_connection

EARTH_RADIUS_METERS = 6371000.0

# Minimum similarity threshold for candidate generation
SIMILARITY_THRESHOLD = 60.0


def _clean_text(text: Optional[str]) -> str:
    """Normalizes text for comparison."""
    if not text:
        return ""
    return re.sub(r"[^\w\s]", " ", text.lower()).strip()


def _get_words(text: Optional[str]) -> set:
    """Extracts a set of distinct words."""
    cleaned = _clean_text(text)
    return set(cleaned.split())


def calculate_jaccard_similarity(text1: Optional[str], text2: Optional[str]) -> float:
    """
    Computes Jaccard similarity coefficient between two texts (0.0 to 1.0).
    """
    w1 = _get_words(text1)
    w2 = _get_words(text2)
    if not w1 or not w2:
        return 0.0
    intersection = len(w1.intersection(w2))
    union = len(w1.union(w2))
    return intersection / union if union > 0 else 0.0


def calculate_haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculates geographic distance in meters between two lat/lon coordinates.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_METERS * c


def calculate_tfidf_similarity(text1: Optional[str], text2: Optional[str]) -> float:
    """
    Computes TF-IDF cosine similarity between two texts (0.0 to 1.0).

    Uses scikit-learn's TfidfVectorizer for proper TF-IDF weighting.
    Returns 0.0 if either text is empty or on error.
    """
    t1 = _clean_text(text1)
    t2 = _clean_text(text2)

    if not t1 or not t2:
        return 0.0

    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([t1, t2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(similarity)
    except Exception:
        # Fall back to Jaccard if TF-IDF fails
        return calculate_jaccard_similarity(text1, text2)


def calculate_complaint_similarity(
    c1: Dict[str, Any], c2: Dict[str, Any]
) -> Tuple[float, Dict[str, Any]]:
    """
    Computes an overall similarity score (0.0 - 100.0) between two complaints.

    Factors:
    - TF-IDF text similarity of Title and Description (weighted)
    - Category match (boost if same category, but not sole criterion)
    - Location proximity:
        - GPS distance if coordinates exist
        - Address text similarity if no GPS

    Returns:
        (total_similarity_score, breakdown_details)
    """
    # 1. TF-IDF Text Similarity (title + description)
    title_sim = calculate_tfidf_similarity(c1.get("title"), c2.get("title"))
    desc_sim = calculate_tfidf_similarity(c1.get("description"), c2.get("description"))
    text_sim = (title_sim * 0.4) + (desc_sim * 0.6)

    # 2. Category Match
    cat_match = 1.0 if c1.get("category") == c2.get("category") else 0.0

    # 3. Location Component
    loc_score = 0.0
    distance_meters = None

    c1_lat, c1_lon = c1.get("latitude"), c1.get("longitude")
    c2_lat, c2_lon = c2.get("latitude"), c2.get("longitude")

    if c1_lat is not None and c1_lon is not None and c2_lat is not None and c2_lon is not None:
        try:
            distance_meters = calculate_haversine_distance(c1_lat, c1_lon, c2_lat, c2_lon)
            if distance_meters <= 100.0:
                loc_score = 1.0
            elif distance_meters <= 300.0:
                loc_score = 0.80
            elif distance_meters <= 600.0:
                loc_score = 0.55
            elif distance_meters <= 1000.0:
                loc_score = 0.30
            else:
                loc_score = 0.0
        except Exception:
            loc_score = 0.0

        # Weighted calculation with GPS (text 40%, category 20%, location 40%)
        total = (text_sim * 40.0) + (cat_match * 20.0) + (loc_score * 40.0)
    else:
        # Address text matching fallback (text 50%, category 25%, address 25%)
        addr_sim = calculate_jaccard_similarity(
            c1.get("location_address"), c2.get("location_address")
        )
        total = (text_sim * 50.0) + (cat_match * 25.0) + (addr_sim * 25.0)

    # Apply category gate: if categories don't match, reduce score significantly
    # (but don't eliminate entirely, as text similarity may still indicate duplicates)
    if not cat_match:
        total = total * 0.5

    final_score = max(0.0, min(100.0, round(total, 1)))

    details = {
        "text_similarity_pct": round(text_sim * 100.0, 1),
        "title_similarity_pct": round(title_sim * 100.0, 1),
        "description_similarity_pct": round(desc_sim * 100.0, 1),
        "category_matched": bool(cat_match),
        "distance_meters": round(distance_meters, 1) if distance_meters is not None else None,
        "location_score_pct": round(loc_score * 100.0, 1),
        "address_similarity_pct": round(calculate_jaccard_similarity(c1.get("location_address"), c2.get("location_address")) * 100.0, 1) if c1_lat is None or c2_lat is None else None,
    }

    return final_score, details


def detect_and_record_duplicates_for_complaint(
    new_complaint_id: int,
    similarity_threshold: float = SIMILARITY_THRESHOLD,
    max_days: int = 90,
) -> List[Dict[str, Any]]:
    """
    Compares the newly created complaint against existing complaints.
    Records any pairs with similarity >= threshold into duplicate_matches.
    Enforces original_complaint_id < duplicate_complaint_id per database constraint.

    Uses TF-IDF text similarity, category matching, and geographic distance.
    Does NOT generate candidates solely because two complaints share a category.
    """
    found_matches = []
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Retrieve target complaint
            cursor.execute("SELECT * FROM complaints WHERE id = ?;", (new_complaint_id,))
            target = cursor.fetchone()
            if not target:
                return []
            target_dict = dict(target)

            # Skip archived or withdrawn complaints
            if target_dict.get("is_archived") or target_dict.get("is_withdrawn"):
                return []

            # Retrieve comparison candidates (excluding itself, within max_days, not resolved/rejected)
            cursor.execute(
                """
                SELECT * FROM complaints
                WHERE id != ?
                  AND status NOT IN ('Resolved', 'Rejected')
                  AND is_archived = 0
                  AND is_withdrawn = 0
                  AND DATE(created_at) >= DATE('now', ? || ' days')
                ORDER BY id ASC;
                """,
                (new_complaint_id, f"-{max_days}"),
            )
            candidates = [dict(r) for r in cursor.fetchall()]

            for candidate in candidates:
                score, details = calculate_complaint_similarity(target_dict, candidate)

                if score >= similarity_threshold:
                    # Enforce constraint: original_complaint_id < duplicate_complaint_id
                    orig_id = min(target_dict["id"], candidate["id"])
                    dup_id = max(target_dict["id"], candidate["id"])

                    # Insert candidate into duplicate_matches safely (ignore duplicates)
                    try:
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO duplicate_matches (
                                original_complaint_id, duplicate_complaint_id,
                                similarity_score, status
                            ) VALUES (?, ?, ?, 'Pending Review');
                            """,
                            (orig_id, dup_id, score),
                        )
                        conn.commit()

                        found_matches.append(
                            {
                                "original_id": orig_id,
                                "duplicate_id": dup_id,
                                "similarity_score": score,
                                "details": details,
                            }
                        )
                    except sqlite3.Error:
                        pass

            return found_matches

    except sqlite3.Error:
        return []


def get_all_duplicate_matches(
    status_filter: Optional[str] = None,
    search_query: Optional[str] = None,
    sort_by: str = "similarity_desc",
    page: int = 1,
    page_size: int = 15,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Retrieves candidate duplicate pairs with enriched complaint information.

    Supports filtering by status, searching by complaint ID/category/location,
    sorting, and pagination.

    Returns:
        (matches_list, total_count)
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Base query
            base_query = """
                SELECT dm.id AS match_id,
                       dm.original_complaint_id,
                       dm.duplicate_complaint_id,
                       dm.similarity_score,
                       dm.status,
                       dm.reviewed_by_admin_id,
                       dm.reviewed_at,
                       dm.created_at AS detected_at,
                       c1.title AS orig_title,
                       c1.category AS orig_category,
                       c1.status AS orig_status,
                       c1.location_address AS orig_address,
                       c1.created_at AS orig_created_at,
                       c1.latitude AS orig_lat,
                       c1.longitude AS orig_lon,
                       c2.title AS dup_title,
                       c2.category AS dup_category,
                       c2.status AS dup_status,
                       c2.location_address AS dup_address,
                       c2.created_at AS dup_created_at,
                       c2.latitude AS dup_lat,
                       c2.longitude AS dup_lon,
                       u.full_name AS reviewer_name
                FROM duplicate_matches dm
                JOIN complaints c1 ON dm.original_complaint_id = c1.id
                JOIN complaints c2 ON dm.duplicate_complaint_id = c2.id
                LEFT JOIN users u ON dm.reviewed_by_admin_id = u.id
                WHERE 1=1
            """
            params: List[Any] = []

            # Status filter
            if status_filter and status_filter != "All":
                base_query += " AND dm.status = ?"
                params.append(status_filter)

            # Search filter
            if search_query and search_query.strip():
                search_term = f"%{search_query.strip()}%"
                base_query += """ AND (
                    CAST(dm.original_complaint_id AS TEXT) LIKE ? OR
                    CAST(dm.duplicate_complaint_id AS TEXT) LIKE ? OR
                    c1.category LIKE ? OR
                    c2.category LIKE ? OR
                    c1.location_address LIKE ? OR
                    c2.location_address LIKE ?
                )"""
                params.extend([search_term] * 6)

            # Sort
            if sort_by == "similarity_desc":
                base_query += " ORDER BY dm.similarity_score DESC, dm.id DESC"
            elif sort_by == "similarity_asc":
                base_query += " ORDER BY dm.similarity_score ASC, dm.id ASC"
            elif sort_by == "newest":
                base_query += " ORDER BY dm.created_at DESC"
            elif sort_by == "oldest":
                base_query += " ORDER BY dm.created_at ASC"

            # Get total count
            count_query = f"SELECT COUNT(*) FROM ({base_query})"
            cursor.execute(count_query, tuple(params))
            total_count = cursor.fetchone()[0]

            # Apply pagination
            offset = (page - 1) * page_size
            paginated_query = base_query + " LIMIT ? OFFSET ?"
            params.extend([page_size, offset])

            cursor.execute(paginated_query, tuple(params))
            matches = [dict(row) for row in cursor.fetchall()]

            return matches, total_count

    except sqlite3.Error:
        return [], 0


def get_duplicate_counts() -> Dict[str, int]:
    """
    Get counts of duplicate matches by status.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, COUNT(*) as cnt FROM duplicate_matches GROUP BY status
            """)
            counts = {"Pending Review": 0, "Confirmed Duplicate": 0, "Marked Not Duplicate": 0, "All": 0}
            for row in cursor.fetchall():
                counts[row["status"]] = row["cnt"]
                counts["All"] += row["cnt"]
            return counts
    except sqlite3.Error:
        return {"Pending Review": 0, "Confirmed Duplicate": 0, "Marked Not Duplicate": 0, "All": 0}


def review_duplicate_match(
    match_id: int,
    admin_id: int,
    decision: str,
    remarks: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Reviews a duplicate match candidate.
    """
    if decision not in ("Confirmed Duplicate", "Marked Not Duplicate"):
        return (
            False,
            "Invalid decision. Must be 'Confirmed Duplicate' or 'Marked Not Duplicate'.",
        )

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT original_complaint_id, duplicate_complaint_id FROM duplicate_matches WHERE id = ?;",
                (match_id,),
            )
            row = cursor.fetchone()
            if not row:
                return False, f"Duplicate match record #{match_id} not found."

            orig_id = row["original_complaint_id"]
            dup_id = row["duplicate_complaint_id"]

            # 1. Update duplicate match record
            cursor.execute(
                """
                UPDATE duplicate_matches
                SET status = ?,
                    reviewed_by_admin_id = ?,
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (decision, admin_id, match_id),
            )

            # 2. Log in admin_actions
            log_note = (
                f"Duplicate review for Ticket #{orig_id} vs #{dup_id}: Marked as '{decision}'. "
                f"Remarks: {remarks.strip() if remarks else 'None'}"
            )
            cursor.execute(
                """
                INSERT INTO admin_actions (
                    admin_id, complaint_id, action_type, action_details
                ) VALUES (?, ?, 'DUPLICATE_REVIEW', ?);
                """,
                (admin_id, dup_id, log_note),
            )

            conn.commit()
            return True, f"Match #{match_id} recorded as '{decision}' successfully."

    except sqlite3.Error as err:
        return False, f"Database error during duplicate review: {err}"


def deduplicate_candidate_rows() -> Tuple[int, int]:
    """
    Safely deduplicate exact repeated duplicate candidate rows.

    Keeps the row with the highest similarity score (or latest created_at
    if scores are equal). Removes exact duplicates (same original/duplicate pair).

    Returns:
        (rows_before, rows_after)
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM duplicate_matches")
            before = cursor.fetchone()[0]

            # Find and remove exact duplicate pairs, keeping the best one
            cursor.execute("""
                DELETE FROM duplicate_matches
                WHERE id NOT IN (
                    SELECT MIN(id) FROM duplicate_matches
                    GROUP BY original_complaint_id, duplicate_complaint_id
                )
            """)
            conn.commit()

            cursor.execute("SELECT COUNT(*) FROM duplicate_matches")
            after = cursor.fetchone()[0]

            return before, after
    except sqlite3.Error:
        return 0, 0


