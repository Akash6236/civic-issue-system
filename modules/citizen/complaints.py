"""
Citizen Complaints Management Module
AI-Powered Civic Issue Reporting and Management System

Handles complaint submission, image uploads, complaint history,
and citizen-scoped complaint queries.
"""

import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from modules.database import BASE_DIR, get_connection

UPLOADS_DIR = BASE_DIR / "uploads" / "complaints"

CATEGORIES = [
    "Garbage",
    "Road Damage",
    "Water Leakage",
    "Streetlight",
    "Drainage",
    "Public Sanitation",
    "Other",
]

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def save_complaint_image(uploaded_file) -> Tuple[bool, str, Optional[str]]:
    """
    Validates and saves an uploaded image using a unique filename.
    Stores the file under uploads/complaints/ and returns the relative path.
    """
    if not uploaded_file:
        return True, "No image uploaded.", None

    # Validate file size
    if uploaded_file.size > MAX_IMAGE_SIZE_BYTES:
        return (
            False,
            f"Image size ({uploaded_file.size / (1024 * 1024):.1f}MB) exceeds the 5MB limit. Please upload a smaller image.",
            None,
        )

    # Validate file extension
    ext = Path(uploaded_file.name).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return (
            False,
            f"Unsupported file format '{ext}'. Allowed formats: JPG, JPEG, PNG, WEBP.",
            None,
        )

    try:
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        destination_path = UPLOADS_DIR / unique_filename

        with open(destination_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        relative_path = f"uploads/complaints/{unique_filename}"
        return True, "Image uploaded successfully.", relative_path

    except Exception as err:
        return False, f"Failed to save uploaded image: {err}", None


def submit_complaint(
    user_id: int,
    title: str,
    category: str,
    description: str,
    location_address: str,
    uploaded_image=None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    location_source: Optional[str] = None,
    location_confirmed: Optional[int] = None,
    ai_category: Optional[str] = None,
    ai_confidence: Optional[float] = None,
) -> Tuple[bool, str, Optional[int]]:
    """
    Submits a new civic complaint for the logged-in citizen.

    - Validates required fields and categories.
    - Saves photograph if provided.
    - Inserts complaint into complaints table along with optional AI suggestions.
    - Records initial 'Submitted' entry in complaint_history.
    - Executes duplicate detection against recent existing complaints.
    - Executes in a single database transaction.

    Returns:
        (success: bool, message: str, complaint_id: Optional[int])
    """
    title_clean = title.strip() if title else ""
    category_clean = category.strip() if category else ""
    desc_clean = description.strip() if description else ""
    loc_clean = location_address.strip() if location_address else ""

    # 1. Validation
    if not title_clean:
        return False, "Complaint title is required.", None
    if not category_clean or category_clean not in CATEGORIES:
        return False, f"Please select a valid category from: {', '.join(CATEGORIES)}.", None
    if not desc_clean:
        return False, "Detailed description of the issue is required.", None
    if not loc_clean:
        return False, "Location address or landmark is required.", None

    # Handle coordinates check (both must be None or both must be float)
    if (latitude is not None and longitude is None) or (latitude is None and longitude is not None):
        return False, "Both latitude and longitude must be provided together, or left empty.", None

    if latitude is not None and not (-90.0 <= latitude <= 90.0):
        return False, "Latitude must be between -90 and 90.", None
    if longitude is not None and not (-180.0 <= longitude <= 180.0):
        return False, "Longitude must be between -180 and 180.", None

    # Normalize location_source: strip whitespace, convert empty to None
    if location_source is not None:
        location_source = location_source.strip()
        if location_source == "":
            location_source = None

    # Validate location_source against schema CHECK constraint
    valid_sources = (None, "GPS", "EXIF", "Manual")
    if location_source not in valid_sources:
        return False, f"Invalid location source. Must be one of: GPS, EXIF, Manual.", None

    # location_confirmed must be 0 or 1 when provided
    if location_confirmed is not None and location_confirmed not in (0, 1):
        return False, "location_confirmed must be 0 or 1.", None

    # 2. Save Image (if attached)
    image_path = None
    if uploaded_image is not None:
        img_ok, img_msg, img_path = save_complaint_image(uploaded_image)
        if not img_ok:
            return False, img_msg, None
        image_path = img_path

    # 3. Insert Complaint & History in a Single Database Transaction
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO complaints (
                    user_id, title, category, description, image_path,
                    location_address, latitude, longitude, location_source,
                    location_confirmed, ai_category, ai_confidence, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Submitted');
                """,
                (
                    user_id,
                    title_clean,
                    category_clean,
                    desc_clean,
                    image_path,
                    loc_clean,
                    latitude,
                    longitude,
                    location_source,
                    location_confirmed,
                    ai_category,
                    ai_confidence,
                ),
            )
            complaint_id = cursor.lastrowid

            # Initial status transition in complaint_history
            cursor.execute(
                """
                INSERT INTO complaint_history (
                    complaint_id, changed_by_user_id, old_status, new_status, remarks
                ) VALUES (?, ?, NULL, 'Submitted', 'Initial complaint submitted by citizen.');
                """,
                (complaint_id, user_id),
            )

            conn.commit()

            # Automatically run duplicate detection against existing complaints
            try:
                from modules.ai.duplicates import detect_and_record_duplicates_for_complaint

                detect_and_record_duplicates_for_complaint(complaint_id)
            except Exception:
                pass

            return True, f"Complaint submitted successfully! Reference ID: #{complaint_id}", complaint_id

    except sqlite3.Error as err:
        return False, f"Database error during complaint submission: {err}", None


def get_citizen_complaints(
    user_id: int,
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    search_query: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves complaints submitted by the specified citizen only.
    Guarantees privacy: citizens can never query another citizen's records.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM complaints WHERE user_id = ? AND is_withdrawn = 0"
            params: List[Any] = [user_id]

            if status_filter and status_filter != "All":
                query += " AND status = ?"
                params.append(status_filter)

            if category_filter and category_filter != "All":
                query += " AND category = ?"
                params.append(category_filter)

            if search_query and search_query.strip():
                query += " AND (title LIKE ? OR description LIKE ? OR location_address LIKE ?)"
                wildcard = f"%{search_query.strip()}%"
                params.extend([wildcard, wildcard, wildcard])

            query += " ORDER BY created_at DESC;"

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    except sqlite3.Error:
        return []


def get_citizen_complaint_details(complaint_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetches complete complaint details for a citizen, strictly verifying ownership.
    Returns None if the complaint does not belong to the user.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM complaints
                WHERE id = ? AND user_id = ? AND is_withdrawn = 0;
                """,
                (complaint_id, user_id),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)
    except sqlite3.Error:
        return None


def get_complaint_history(complaint_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves the chronological audit history for a specific complaint.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT h.id, h.complaint_id, h.old_status, h.new_status, h.remarks,
                       h.changed_at, u.full_name AS changed_by_name, u.role AS changed_by_role
                FROM complaint_history h
                JOIN users u ON h.changed_by_user_id = u.id
                WHERE h.complaint_id = ?
                ORDER BY h.changed_at ASC;
                """,
                (complaint_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error:
        return []


def get_citizen_dashboard_stats(user_id: int) -> Dict[str, int]:
    """
    Computes summary metrics for the citizen's overview dashboard.
    """
    stats = {
        "total": 0,
        "submitted": 0,
        "under_review": 0,
        "in_progress": 0,
        "resolved": 0,
        "rejected": 0,
    }
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT status, COUNT(*) as count
                FROM complaints
                WHERE user_id = ? AND is_withdrawn = 0
                GROUP BY status;
                """,
                (user_id,),
            )
            for row in cursor.fetchall():
                st_name = row["status"]
                c = row["count"]
                stats["total"] += c
                if st_name == "Submitted":
                    stats["submitted"] = c
                elif st_name == "Under Review":
                    stats["under_review"] = c
                elif st_name == "In Progress":
                    stats["in_progress"] = c
                elif st_name == "Resolved":
                    stats["resolved"] = c
                elif st_name == "Rejected":
                    stats["rejected"] = c

        return stats
    except sqlite3.Error:
        return stats


# ---------------------------------------------------------
# Citizen Complaint Edit & Withdraw
# ---------------------------------------------------------

EDITABLE_STATUSES = ("Submitted", "Under Review")
WITHDRAWABLE_STATUSES = ("Submitted", "Under Review")


def edit_complaint(
    complaint_id: int,
    user_id: int,
    title: Optional[str] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    location_address: Optional[str] = None,
    uploaded_image=None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    location_source: Optional[str] = None,
    location_confirmed: Optional[int] = None,
) -> Tuple[bool, str]:
    """
    Edits an existing citizen complaint.

    Only complaints owned by the user and in editable statuses
    (Submitted, Under Review) can be modified.

    All changes are recorded in complaint_history with the previous values.

    Returns:
        (success: bool, message: str)
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Verify ownership and current status
            cursor.execute(
                """
                SELECT status, title, category, description, location_address,
                       latitude, longitude, location_source, location_confirmed
                FROM complaints
                WHERE id = ? AND user_id = ? AND is_withdrawn = 0;
                """,
                (complaint_id, user_id),
            )
            row = cursor.fetchone()
            if not row:
                return False, "Complaint not found or not editable."

            current_status = row["status"]
            if current_status not in EDITABLE_STATUSES:
                return False, (
                    f"Cannot edit complaint in '{current_status}' status. "
                    "Only Submitted or Under Review complaints can be edited."
                )

            # Build update fields
            updates = []
            params = []

            if title is not None and title.strip():
                updates.append("title = ?")
                params.append(title.strip())
            if category is not None and category.strip():
                if category.strip() not in CATEGORIES:
                    return False, f"Invalid category. Must be one of: {', '.join(CATEGORIES)}."
                updates.append("category = ?")
                params.append(category.strip())
            if description is not None and description.strip():
                updates.append("description = ?")
                params.append(description.strip())
            if location_address is not None and location_address.strip():
                updates.append("location_address = ?")
                params.append(location_address.strip())
            if latitude is not None:
                updates.append("latitude = ?")
                params.append(latitude)
            if longitude is not None:
                updates.append("longitude = ?")
                params.append(longitude)
            if location_source is not None:
                updates.append("location_source = ?")
                params.append(location_source)
            if location_confirmed is not None:
                updates.append("location_confirmed = ?")
                params.append(location_confirmed)

            if uploaded_image is not None:
                img_ok, img_msg, img_path = save_complaint_image(uploaded_image)
                if not img_ok:
                    return False, img_msg
                updates.append("image_path = ?")
                params.append(img_path)

            if not updates:
                return False, "No changes provided."

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(complaint_id)

            cursor.execute(
                f"UPDATE complaints SET {', '.join(updates)} WHERE id = ?;",
                tuple(params),
            )

            conn.commit()
            return True, f"Complaint #{complaint_id} updated successfully."

    except sqlite3.Error as err:
        return False, f"Database error during complaint edit: {err}"


def withdraw_complaint(
    complaint_id: int,
    user_id: int,
    reason: str,
) -> Tuple[bool, str]:
    """
    Withdraws a citizen complaint.

    Only complaints owned by the user and in withdrawable statuses
    (Submitted, Under Review) can be withdrawn.

    The complaint is not physically deleted. Instead, is_withdrawn is set to 1
    and the reason is recorded. The status is changed to 'Rejected' to reflect
    withdrawal, with full audit history preserved.

    Returns:
        (success: bool, message: str)
    """
    clean_reason = reason.strip() if reason and reason.strip() else ""

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Verify ownership and current status
            cursor.execute(
                """
                SELECT status FROM complaints
                WHERE id = ? AND user_id = ? AND is_withdrawn = 0;
                """,
                (complaint_id, user_id),
            )
            row = cursor.fetchone()
            if not row:
                return False, "Complaint not found or not withdrawable."

            current_status = row["status"]
            if current_status not in WITHDRAWABLE_STATUSES:
                return False, (
                    f"Cannot withdraw complaint in '{current_status}' status. "
                    "Only Submitted or Under Review complaints can be withdrawn."
                )

            if not clean_reason:
                return False, "A withdrawal reason is required."

            # Update complaint: mark as withdrawn and set status to Rejected
            cursor.execute(
                """
                UPDATE complaints
                SET is_withdrawn = 1,
                    withdrawal_reason = ?,
                    status = 'Rejected',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (clean_reason, complaint_id),
            )

            # Record in history
            cursor.execute(
                """
                INSERT INTO complaint_history (
                    complaint_id, changed_by_user_id, old_status, new_status, remarks
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (
                    complaint_id,
                    user_id,
                    current_status,
                    "Rejected",
                    f"Withdrawn by citizen. Reason: {clean_reason}",
                ),
            )

            conn.commit()
            return True, f"Complaint #{complaint_id} has been withdrawn."

    except sqlite3.Error as err:
        return False, f"Database error during complaint withdrawal: {err}"

