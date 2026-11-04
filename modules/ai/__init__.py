"""
AI Module Package
AI-Powered Civic Issue Reporting and Management System
"""

from modules.ai.classification import CATEGORIES, classify_complaint
from modules.ai.duplicates import (
    calculate_complaint_similarity,
    calculate_haversine_distance,
    calculate_jaccard_similarity,
    detect_and_record_duplicates_for_complaint,
    get_all_duplicate_matches,
    review_duplicate_match,
)

__all__ = [
    "CATEGORIES",
    "classify_complaint",
    "calculate_jaccard_similarity",
    "calculate_haversine_distance",
    "calculate_complaint_similarity",
    "detect_and_record_duplicates_for_complaint",
    "get_all_duplicate_matches",
    "review_duplicate_match",
]

