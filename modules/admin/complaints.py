"""
Admin Complaints Management Module
AI-Powered Civic Issue Reporting and Management System

Handles administration oversight, search/filter, complaint review,
status transitions with history auditing, and administrative action logs.
"""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from modules.database import get_connection
from modules.citizen.complaints import CATEGORIES

VALID_STATUSES = [
    "Submitted",
    "Under Review",
    "Approved",
    "In Progress",
    "Resolved",
    "Rejected",
]


def get_all_complaints(
    search_query: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves all civic complaints with citizen metadata for administrative review.
    Supports search across ticket ID, title, description, address, and citizen name.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT c.*,
                        u.full_name AS citizen_name,
                        u.email AS citizen_email,
                        u.phone AS citizen_phone
                FROM complaints c
                JOIN users u ON c.user_id = u.id
                WHERE c.is_archived = 0 AND c.is_withdrawn = 0
            """
            params: List[Any] = []

            if category and category != "All":
                query += " AND c.category = ?"
                params.append(category)

            if status and status != "All":
                query += " AND c.status = ?"
                params.append(status)

            if date_from:
                query += " AND DATE(c.created_at) >= DATE(?)"
                params.append(date_from)

            if date_to:
                query += " AND DATE(c.created_at) <= DATE(?)"
                params.append(date_to)

            if search_query and search_query.strip():
                clean_term = search_query.strip()
                query += """
                    AND (
                        CAST(c.id AS TEXT) = ?
                        OR c.title LIKE ?
                        OR c.description LIKE ?
                        OR c.location_address LIKE ?
                        OR u.full_name LIKE ?
                        OR u.email LIKE ?
                    )
                """
                wildcard = f"%{clean_term}%"
                params.extend([clean_term, wildcard, wildcard, wildcard, wildcard, wildcard])

            query += " ORDER BY c.created_at DESC;"

            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]

    except sqlite3.Error:
        return []


def get_complaint_details_for_admin(complaint_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves complete complaint details including citizen contact details.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT c.*,
                       u.full_name AS citizen_name,
                       u.email AS citizen_email,
                       u.phone AS citizen_phone
                FROM complaints c
                JOIN users u ON c.user_id = u.id
                WHERE c.id = ?;
                """,
                (complaint_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)
    except sqlite3.Error:
        return None


def update_complaint_status(
    complaint_id: int,
    admin_id: int,
    new_status: str,
    remarks: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Updates the complaint status and audits the transition.

    Guarantees:
    - Status must be in approved lifecycle list.
    - Status cannot be updated to the exact same status.
    - Updates complaints.status and updated_at.
    - Records old and new status with remarks in complaint_history.
    - Records the action in admin_actions.
    - All three operations commit atomically in a single transaction.

    Returns:
        (success: bool, message: str)
    """
    if new_status not in VALID_STATUSES:
        return False, f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}."

    clean_remarks = remarks.strip() if remarks and remarks.strip() else "Status updated by administrator."

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # 1. Fetch current status
            cursor.execute("SELECT status FROM complaints WHERE id = ?;", (complaint_id,))
            row = cursor.fetchone()
            if not row:
                return False, f"Complaint #{complaint_id} not found."

            old_status = row["status"]
            if old_status == new_status:
                return False, f"Complaint #{complaint_id} is already in '{new_status}' status."

            # 2. Update complaint record
            cursor.execute(
                """
                UPDATE complaints
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (new_status, complaint_id),
            )

            # 3. Insert audit log in complaint_history
            cursor.execute(
                """
                INSERT INTO complaint_history (
                    complaint_id, changed_by_user_id, old_status, new_status, remarks
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (complaint_id, admin_id, old_status, new_status, clean_remarks),
            )

            # 4. Insert record in admin_actions
            action_desc = f"Changed status from '{old_status}' to '{new_status}'. Remarks: {clean_remarks}"
            cursor.execute(
                """
                INSERT INTO admin_actions (
                    admin_id, complaint_id, action_type, action_details
                ) VALUES (?, ?, 'STATUS_UPDATE', ?);
                """,
                (admin_id, complaint_id, action_desc),
            )

            conn.commit()
            return True, f"Complaint #{complaint_id} status updated to '{new_status}'."

    except sqlite3.Error as err:
        return False, f"Database error during status update: {err}"


def get_admin_dashboard_stats() -> Dict[str, Any]:
    """
    Aggregates municipal operational metrics.
    """
    stats = {
        "total": 0,
        "submitted": 0,
        "under_review": 0,
        "approved": 0,
        "in_progress": 0,
        "resolved": 0,
        "rejected": 0,
        "total_citizens": 0,
    }
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Complaint counts by status
            cursor.execute("SELECT status, COUNT(*) as cnt FROM complaints GROUP BY status;")
            for row in cursor.fetchall():
                st_name = row["status"]
                c = row["cnt"]
                stats["total"] += c
                if st_name == "Submitted":
                    stats["submitted"] = c
                elif st_name == "Under Review":
                    stats["under_review"] = c
                elif st_name == "Approved":
                    stats["approved"] = c
                elif st_name == "In Progress":
                    stats["in_progress"] = c
                elif st_name == "Resolved":
                    stats["resolved"] = c
                elif st_name == "Rejected":
                    stats["rejected"] = c

            # Total registered citizens
            cursor.execute("SELECT COUNT(*) as citizen_count FROM users WHERE role = 'citizen';")
            row = cursor.fetchone()
            if row:
                stats["total_citizens"] = row["citizen_count"]

        return stats
    except sqlite3.Error:
        return stats


def get_admin_audit_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieves the administrative activity audit trail.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.id, a.admin_id, a.complaint_id, a.action_type,
                        a.action_details, a.action_timestamp,
                        u.full_name AS admin_name, u.email AS admin_email,
                        c.title AS complaint_title
                FROM admin_actions a
                JOIN users u ON a.admin_id = u.id
                LEFT JOIN complaints c ON a.complaint_id = c.id
                ORDER BY a.action_timestamp DESC
                LIMIT ?;
                """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error:
        return []


# ---------------------------------------------------------
# Admin Complaint Edit & Archive
# ---------------------------------------------------------

def edit_complaint_admin(
    complaint_id: int,
    admin_id: int,
    title: Optional[str] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    location_address: Optional[str] = None,
    status: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Edits an existing complaint (admin override).

    Admin can edit any complaint field. Changes are recorded in
    complaint_history and admin_actions.

    Returns:
        (success: bool, message: str)
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Verify complaint exists
            cursor.execute(
                "SELECT status, title, category, description, location_address FROM complaints WHERE id = ?;",
                (complaint_id,),
            )
            row = cursor.fetchone()
            if not row:
                return False, f"Complaint #{complaint_id} not found."

            old_status = row["status"]
            old_values = {
                "title": row["title"],
                "category": row["category"],
                "description": row["description"],
                "location_address": row["location_address"],
            }

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
            if status is not None and status in VALID_STATUSES:
                if status != old_status:
                    updates.append("status = ?")
                    params.append(status)

            if not updates:
                return False, "No changes provided."

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(complaint_id)

            cursor.execute(
                f"UPDATE complaints SET {', '.join(updates)} WHERE id = ?;",
                tuple(params),
            )

            # Record in complaint_history if status changed
            new_status = status if status is not None and status in VALID_STATUSES else old_status
            if new_status != old_status:
                cursor.execute(
                    """
                    INSERT INTO complaint_history (
                        complaint_id, changed_by_user_id, old_status, new_status, remarks
                    ) VALUES (?, ?, ?, ?, ?);
                    """,
                    (
                        complaint_id,
                        admin_id,
                        old_status,
                        new_status,
                        "Complaint status updated by administrator.",
                    ),
                )

            # Record in admin_actions
            changed_fields = []
            for field, old_val in old_values.items():
                if field == "title" and title is not None and title.strip():
                    changed_fields.append(f"title: '{old_val}' -> '{title.strip()}'")
                elif field == "category" and category is not None and category.strip():
                    changed_fields.append(f"category: '{old_val}' -> '{category.strip()}'")
                elif field == "description" and description is not None and description.strip():
                    changed_fields.append(f"description: '{old_val}' -> '{description.strip()}'")
                elif field == "location_address" and location_address is not None and location_address.strip():
                    changed_fields.append(f"location_address: '{old_val}' -> '{location_address.strip()}'")

            action_desc = f"Admin edited complaint #{complaint_id}. "
            if changed_fields:
                action_desc += "Changed: " + "; ".join(changed_fields)
            if new_status != old_status:
                action_desc += f" Status: '{old_status}' -> '{new_status}'."

            cursor.execute(
                """
                INSERT INTO admin_actions (
                    admin_id, complaint_id, action_type, action_details
                ) VALUES (?, ?, 'ADMIN_EDIT', ?);
                """,
                (admin_id, complaint_id, action_desc),
            )

            conn.commit()
            return True, f"Complaint #{complaint_id} updated successfully."

    except sqlite3.Error as err:
        return False, f"Database error during complaint edit: {err}"


def archive_complaint(
    complaint_id: int,
    admin_id: int,
    reason: str,
) -> Tuple[bool, str]:
    """
    Archives a complaint (admin action).

    The complaint is not physically deleted. Instead, is_archived is set to 1
    and the reason is recorded. Archived complaints are hidden from normal views.

    Returns:
        (success: bool, message: str)
    """
    clean_reason = reason.strip() if reason and reason.strip() else ""

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Verify complaint exists and is not already archived
            cursor.execute(
                "SELECT status, is_archived FROM complaints WHERE id = ?;",
                (complaint_id,),
            )
            row = cursor.fetchone()
            if not row:
                return False, f"Complaint #{complaint_id} not found."

            if row["is_archived"]:
                return False, f"Complaint #{complaint_id} is already archived."

            old_status = row["status"]

            # Archive the complaint
            cursor.execute(
                """
                UPDATE complaints
                SET is_archived = 1,
                    archive_reason = ?,
                    status = 'Rejected',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (clean_reason, complaint_id),
            )

            # Record in complaint_history
            cursor.execute(
                """
                INSERT INTO complaint_history (
                    complaint_id, changed_by_user_id, old_status, new_status, remarks
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (
                    complaint_id,
                    admin_id,
                    old_status,
                    "Rejected",
                    f"Archived by administrator. Reason: {clean_reason}",
                ),
            )

            # Record in admin_actions
            action_desc = f"Archived complaint #{complaint_id}. Reason: {clean_reason}"
            cursor.execute(
                """
                INSERT INTO admin_actions (
                    admin_id, complaint_id, action_type, action_details
                ) VALUES (?, ?, 'ARCHIVE', ?);
                """,
                (admin_id, complaint_id, action_desc),
            )

            conn.commit()
            return True, f"Complaint #{complaint_id} has been archived."

    except sqlite3.Error as err:
        return False, f"Database error during complaint archive: {err}"


def get_archived_complaints() -> List[Dict[str, Any]]:
    """
    Retrieves all archived complaints with citizen metadata.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT c.*,
                       u.full_name AS citizen_name,
                       u.email AS citizen_email
                FROM complaints c
                JOIN users u ON c.user_id = u.id
                WHERE c.is_archived = 1
                ORDER BY c.updated_at DESC;
                """
            )
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error:
        return []

