"""
Image-Based Civic Issue Classification Module
AI-Powered Civic Issue Reporting and Management System

Provides lightweight, local image classification for civic complaints using
PIL-based feature extraction and heuristic rules.

IMPORTANT LIMITATIONS:
- This is NOT a deep learning model. It uses handcrafted image features
  (color histograms, edge density, brightness, saturation) and rule-based
  heuristics to suggest categories.
- Confidence scores are intentionally conservative to reflect the
  limitations of heuristic classification.
- No external model downloads, no cloud APIs, no paid services.
- Always runs locally on CPU.

Required image categories:
1. Pothole / Road Damage
2. Garbage / Waste Accumulation
3. Drainage / Waterlogging
4. Water Leakage
5. Streetlight Problem
6. Public Sanitation
7. Other / Uncertain
"""

import math
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageStat, ImageFilter

# Image categories matching the complaint system
IMAGE_CATEGORIES = [
    "Road Damage",
    "Garbage",
    "Water Leakage",
    "Streetlight",
    "Drainage",
    "Public Sanitation",
    "Other",
]

# Mapping from image categories to complaint categories
IMAGE_TO_COMPLAINT_CATEGORY = {
    "Road Damage": "Road Damage",
    "Garbage": "Garbage",
    "Water Leakage": "Water Leakage",
    "Streetlight": "Streetlight",
    "Drainage": "Drainage",
    "Public Sanitation": "Public Sanitation",
    "Other": "Other",
}


def load_image_from_upload(uploaded_file) -> Optional[Image.Image]:
    """
    Load an uploaded image file into a PIL Image object.

    Returns the Image object or None if loading fails.
    """
    if uploaded_file is None:
        return None

    try:
        uploaded_file.seek(0)
        img = Image.open(BytesIO(uploaded_file.read()))
        # Convert to RGB for consistent processing
        if img.mode != "RGB":
            img = img.convert("RGB")
        return img
    except Exception:
        return None


def _extract_color_features(img: Image.Image) -> Dict[str, float]:
    """
    Extract basic color features from an image.

    Features:
    - Mean RGB values
    - Standard deviation of RGB (texture/variety indicator)
    - Dominant hue direction (which color channel is strongest)
    - Brightness (overall luminance)
    - Saturation (color intensity)
    """
    stat = ImageStat.Stat(img)
    r, g, b = stat.mean[:3]
    r_std, g_std, b_std = stat.stddev[:3]

    # Overall brightness (luminance)
    brightness = 0.299 * r + 0.587 * g + 0.114 * b

    # Saturation (simplified: max - min of RGB channels)
    saturation = max(r, g, b) - min(r, g, b)

    # Dominant channel
    dominant = max(r, g, b)
    if dominant == r:
        dominant_channel = "red"
    elif dominant == g:
        dominant_channel = "green"
    else:
        dominant_channel = "blue"

    # Gray-ness (how close R, G, B are to each other)
    gray_scale = abs(r - g) + abs(g - b) + abs(b - r)

    return {
        "mean_r": r,
        "mean_g": g,
        "mean_b": b,
        "std_r": r_std,
        "std_g": g_std,
        "std_b": b_std,
        "brightness": brightness,
        "saturation": saturation,
        "dominant_channel": dominant_channel,
        "gray_scale": gray_scale,
    }


def _extract_edge_features(img: Image.Image) -> Dict[str, float]:
    """
    Extract edge/texture features from an image.

    Uses edge detection filter to estimate structural complexity.
    Higher edge density suggests man-made structures (roads, buildings).
    Lower edge density suggests natural or uniform surfaces.
    """
    # Apply edge detection filter
    edges = img.filter(ImageFilter.FIND_EDGES)
    edge_stat = ImageStat.Stat(edges)
    edge_mean = sum(edge_stat.mean[:3]) / 3.0

    # Apply blur and compare to original for detail measure
    blurred = img.filter(ImageFilter.BLUR)
    blur_stat = ImageStat.Stat(blurred)
    orig_stat = ImageStat.Stat(img)

    # Detail = difference between original and blurred
    detail = sum(abs(orig_stat.mean[i] - blur_stat.mean[i]) for i in range(3)) / 3.0

    return {
        "edge_density": edge_mean,
        "detail": detail,
    }


def _heuristic_classify(
    color_feat: Dict[str, float],
    edge_feat: Dict[str, float],
) -> Tuple[str, float, Dict[str, float]]:
    """
    Classify image using rule-based heuristics.

    This is a transparent, explainable classifier (not a trained ML model).
    Each category gets a score based on feature patterns, and the highest
    scoring category is returned with a conservative confidence score.

    Returns:
        (predicted_category, confidence_score, all_category_scores)
    """
    scores: Dict[str, float] = {cat: 0.0 for cat in IMAGE_CATEGORIES}

    brightness = color_feat["brightness"]
    saturation = color_feat["saturation"]
    gray_scale = color_feat["gray_scale"]
    edge_density = edge_feat["edge_density"]
    detail = edge_feat["detail"]
    dominant = color_feat["dominant_channel"]
    mean_r = color_feat["mean_r"]
    mean_g = color_feat["mean_g"]
    mean_b = color_feat["mean_b"]

    # Road Damage: Gray/dark, high edge density (cracks, potholes, asphalt)
    road_score = 0.0
    if gray_scale < 60:  # Near-gray tones
        road_score += 2.0
    if edge_density > 30:  # Structural edges
        road_score += 2.0
    if brightness < 120:  # Darker surfaces
        road_score += 1.0
    if dominant in ("red", "blue"):  # Asphalt tones
        road_score += 0.5
    scores["Road Damage"] = road_score

    # Garbage: Mixed colors, green/brown tones, cluttered (high detail)
    garbage_score = 0.0
    if saturation > 40:  # Colorful/mixed
        garbage_score += 1.0
    if detail > 15:  # Cluttered appearance
        garbage_score += 1.5
    if mean_g > mean_r and mean_g > mean_b:  # Greenish (vegetation/waste)
        garbage_score += 1.0
    if brightness > 80 and brightness < 200:  # Mid-range brightness
        garbage_score += 0.5
    scores["Garbage"] = garbage_score

    # Water Leakage: Blue tones, reflective, lower edge density (smooth water)
    water_score = 0.0
    if mean_b > mean_r and mean_b > mean_g:  # Bluish
        water_score += 2.0
    if brightness > 100:  # Water reflects light
        water_score += 1.0
    if edge_density < 25:  # Smooth surfaces
        water_score += 1.0
    scores["Water Leakage"] = water_score

    # Streetlight: Dark with yellow/white spots (night scenes, lamps)
    streetlight_score = 0.0
    if brightness < 100:  # Dark scenes
        streetlight_score += 1.5
    if saturation > 50 and dominant == "red":  # Yellow/orange lights
        streetlight_score += 1.5
    if edge_density > 20:  # Pole-like structures
        streetlight_score += 0.5
    scores["Streetlight"] = streetlight_score

    # Drainage: Gray/green, grate patterns, water accumulation
    drainage_score = 0.0
    if gray_scale < 80:  # Near-gray or greenish-gray
        drainage_score += 1.0
    if mean_g > 80 and mean_g < 140:  # Dull green
        drainage_score += 1.0
    if edge_density > 25:  # Grate-like patterns
        drainage_score += 1.0
    scores["Drainage"] = drainage_score

    # Public Sanitation: White/beige (toilets, sanitary fixtures)
    sanitation_score = 0.0
    if brightness > 200:  # Very bright (white porcelain)
        sanitation_score += 1.5
    if gray_scale < 30:  # Very neutral (white/off-white)
        sanitation_score += 1.0
    if saturation < 30:  # Low color
        sanitation_score += 0.5
    scores["Public Sanitation"] = sanitation_score

    # Other: Fallback for anything that doesn't match well
    other_score = 0.0
    # Lower score means it's more likely to be "Other" if nothing else matches
    max_other = max(road_score, garbage_score, water_score, streetlight_score,
                    drainage_score, sanitation_score)
    if max_other < 2.0:
        other_score = 3.0 - max_other
    scores["Other"] = other_score

    # Determine best category
    best_category = max(scores, key=lambda k: scores[k])
    best_score = scores[best_category]

    # Convert raw score to conservative confidence (0.0 to 1.0)
    # Heuristic scores are typically 0-5, so we scale conservatively
    confidence = min(0.65, best_score / 8.0)
    confidence = max(0.15, confidence)  # Minimum confidence to show something

    # If top score is very low, mark as uncertain
    if best_score < 1.0:
        best_category = "Other"
        confidence = 0.20

    return best_category, round(confidence, 2), {k: round(v, 2) for k, v in scores.items()}


def classify_image(uploaded_file) -> Tuple[Optional[str], Optional[float], Dict[str, float], Optional[Image.Image]]:
    """
    Classify an uploaded image using local feature extraction and heuristics.

    This is a transparent, rule-based classifier - NOT a trained ML model.
    Confidence scores are conservative to reflect the limitations.

    Args:
        uploaded_file: Streamlit uploaded file object.

    Returns:
        (predicted_category, confidence_score, all_scores, pil_image)
        predicted_category: One of IMAGE_CATEGORIES or None if image can't be loaded
        confidence_score: Conservative confidence between 0.0 and 1.0
        all_scores: Raw heuristic scores for all categories
        pil_image: The loaded PIL Image object (or None)
    """
    img = load_image_from_upload(uploaded_file)
    if img is None:
        return None, None, {}, None

    try:
        color_feat = _extract_color_features(img)
        edge_feat = _extract_edge_features(img)
        category, confidence, scores = _heuristic_classify(color_feat, edge_feat)
        return category, confidence, scores, img
    except Exception:
        return None, None, {}, img


def get_category_color(category: str) -> str:
    """
    Return a display color for an image category.
    """
    color_map = {
        "Road Damage": "#B7A98F",      # Muted sand
        "Garbage": "#34483D",          # Forest green
        "Water Leakage": "#E9EFF4",    # Muted blue
        "Streetlight": "#F6F0E3",      # Soft beige
        "Drainage": "#B7A98F",         # Muted sand
        "Public Sanitation": "#F8EDE7", # Soft terracotta
        "Other": "#D8D6CF",            # Border light
    }
    return color_map.get(category, "#D8D6CF")


def get_category_icon(category: str) -> str:
    """
    Return a simple text icon for an image category.
    """
    icon_map = {
        "Road Damage": "\u26A0",    # ⚠
        "Garbage": "\uD83D\uDDD2",   # 🗑
        "Water Leakage": "\uD83D\uDC7A", # 📺 (placeholder)
        "Streetlight": "\uD83D\uDD06", # 🔆
        "Drainage": "\uD83D\uDE2D",   # 😭 (placeholder)
        "Public Sanitation": "\uD83D\uDEAB", # 🚫 (placeholder)
        "Other": "\u2753",            # ❓
    }
    return icon_map.get(category, "\u2753")


def compare_image_and_text(
    image_category: Optional[str],
    text_category: str,
    image_confidence: Optional[float],
) -> Dict[str, Any]:
    """
    Compare image classification with text classification.

    Returns a dict with:
    - consistent: bool (categories match)
    - warning_message: str or None
    - suggestion: str (recommended category)
    """
    result = {
        "consistent": True,
        "warning_message": None,
        "suggestion": text_category,
    }

    if image_category is None:
        result["consistent"] = False
        result["warning_message"] = (
            "Image could not be classified. Using text-based category instead."
        )
        result["suggestion"] = text_category
        return result

    if image_category != text_category:
        result["consistent"] = False
        if image_confidence is not None and image_confidence < 0.40:
            result["warning_message"] = (
                f"Image suggests '{image_category}' (low confidence: {int(image_confidence * 100)}%), "
                f"but text describes '{text_category}'. "
                "Please verify the category before submitting."
            )
            result["suggestion"] = text_category
        else:
            result["warning_message"] = (
                f"Image suggests '{image_category}' (confidence: {int(image_confidence * 100)}%), "
                f"but text describes '{text_category}'. "
                "These don't match - please confirm the correct category."
            )
            result["suggestion"] = text_category

    return result


def generate_suggested_title(image_category: Optional[str]) -> str:
    """
    Generate a suggested complaint title based on image classification.

    Returns a template title (clearly not AI-generated visual analysis).
    """
    if image_category is None:
        return "Civic Issue Reported"

    title_map = {
        "Road Damage": "Road damage reported",
        "Garbage": "Garbage accumulation reported",
        "Water Leakage": "Water leakage reported",
        "Streetlight": "Streetlight problem reported",
        "Drainage": "Drainage issue reported",
        "Public Sanitation": "Sanitation issue reported",
        "Other": "Civic issue reported",
    }
    return title_map.get(image_category, "Civic Issue Reported")


def generate_suggested_description(
    image_category: Optional[str],
    image_confidence: Optional[float],
) -> str:
    """
    Generate a suggested complaint description based on image classification.

    Returns a template description - clearly NOT AI-generated visual analysis.
    Does not invent location, severity, causes, or damage details.
    """
    if image_category is None:
        return (
            "A civic issue has been reported. "
            "Please inspect the reported location and assess whether action is required."
        )

    desc_map = {
        "Road Damage": (
            "A visible road surface defect has been identified in the uploaded image. "
            "Please inspect the reported location and assess whether repair is required."
        ),
        "Garbage": (
            "Waste accumulation has been identified in the uploaded image. "
            "Please inspect the reported location and assess whether cleanup is required."
        ),
        "Water Leakage": (
            "Possible water leakage has been identified in the uploaded image. "
            "Please inspect the reported location and assess whether repair is required."
        ),
        "Streetlight": (
            "A possible streetlight issue has been identified in the uploaded image. "
            "Please inspect the reported location and assess whether repair is required."
        ),
        "Drainage": (
            "A possible drainage issue has been identified in the uploaded image. "
            "Please inspect the reported location and assess whether maintenance is required."
        ),
        "Public Sanitation": (
            "A possible sanitation issue has been identified in the uploaded image. "
            "Please inspect the reported location and assess whether cleaning is required."
        ),
        "Other": (
            "A civic issue has been identified in the uploaded image. "
            "Please inspect the reported location and assess whether action is required."
        ),
    }

    base_desc = desc_map.get(image_category, desc_map["Other"])

    # Add uncertainty note if confidence is low
    if image_confidence is not None and image_confidence < 0.50:
        base_desc += (
            f"\n\nNote: Image-based category suggestion is '{image_category}' "
            f"with low confidence ({int(image_confidence * 100)}%). "
            "Please verify the correct category."
        )

    return base_desc
