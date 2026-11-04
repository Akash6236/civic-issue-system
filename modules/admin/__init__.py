"""
Admin Module Package
AI-Powered Civic Issue Reporting and Management System
"""

from modules.admin.complaints import (
    VALID_STATUSES,
    get_admin_audit_logs,
    get_admin_dashboard_stats,
    get_all_complaints,
    get_complaint_details_for_admin,
    update_complaint_status,
)

__all__ = [
    "VALID_STATUSES",
    "get_all_complaints",
    "get_complaint_details_for_admin",
    "update_complaint_status",
    "get_admin_dashboard_stats",
    "get_admin_audit_logs",
]

