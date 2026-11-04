"""
AI Category Classification Module
AI-Powered Civic Issue Reporting and Management System

Provides lightweight, local text classification for civic complaints.
Analyzes titles and descriptions to suggest municipal categories with
confidence scores without relying on external cloud APIs or paid models.
"""

import math
import re
from typing import Dict, List, Optional, Tuple

CATEGORIES = [
    "Garbage",
    "Road Damage",
    "Water Leakage",
    "Streetlight",
    "Drainage",
    "Public Sanitation",
    "Other",
]

# Domain-specific keyword and n-gram profiles with importance weights
CATEGORY_KEYWORD_PROFILES: Dict[str, Dict[str, float]] = {
    "Garbage": {
        "garbage": 3.0,
        "trash": 3.0,
        "waste": 2.5,
        "dustbin": 3.0,
        "bin": 2.0,
        "dump": 2.5,
        "litter": 2.5,
        "debris": 2.0,
        "plastic": 1.5,
        "landfill": 2.5,
        "rubbish": 2.5,
        "rotting": 2.0,
        "refuse": 2.0,
        "sweep": 1.5,
        "uncollected": 2.5,
        "pile": 1.5,
        "heap": 1.5,
        "overflowing bin": 4.0,
        "garbage dump": 4.0,
        "solid waste": 3.5,
        "waste disposal": 3.5,
    },
    "Road Damage": {
        "pothole": 3.5,
        "road": 2.0,
        "asphalt": 2.5,
        "tar": 2.0,
        "crater": 3.0,
        "crack": 2.0,
        "pavement": 2.5,
        "sidewalk": 2.0,
        "footpath": 2.0,
        "divider": 2.0,
        "cave in": 3.5,
        "cavein": 3.0,
        "speed breaker": 3.0,
        "speedbreaker": 3.0,
        "uneven": 1.5,
        "damaged road": 4.0,
        "broken road": 4.0,
        "bad road": 3.5,
        "resurfacing": 2.5,
        "accident prone": 2.5,
    },
    "Water Leakage": {
        "leak": 3.0,
        "leakage": 3.5,
        "pipe": 2.5,
        "pipeline": 3.0,
        "burst": 3.5,
        "tap": 2.5,
        "drinking water": 3.5,
        "dripping": 2.0,
        "mainline": 3.0,
        "water supply": 3.5,
        "valve": 2.5,
        "water pressure": 2.5,
        "flooding water": 2.5,
        "broken pipe": 4.0,
        "pipe burst": 4.0,
        "water wastage": 3.5,
        "gushing": 3.0,
    },
    "Streetlight": {
        "streetlight": 3.5,
        "street light": 4.0,
        "light": 2.0,
        "lamp": 3.0,
        "lamppost": 3.5,
        "pole": 2.0,
        "bulb": 2.5,
        "dark": 2.5,
        "darkness": 2.5,
        "blackout": 3.0,
        "flickering": 3.0,
        "night": 1.5,
        "wiring": 2.0,
        "not working": 2.5,
        "broken light": 3.5,
        "no lighting": 3.5,
        "illumination": 2.5,
    },
    "Drainage": {
        "drain": 3.0,
        "drainage": 3.5,
        "gutter": 3.0,
        "sewer": 3.5,
        "sewage": 3.5,
        "clog": 3.0,
        "clogged": 3.0,
        "blockage": 3.0,
        "manhole": 3.5,
        "overflow": 3.0,
        "stormwater": 3.0,
        "stagnant": 2.5,
        "wastewater": 3.0,
        "sewer line": 4.0,
        "storm drain": 4.0,
        "clogged drain": 4.0,
        "overflowing drain": 4.0,
        "foul water": 2.5,
    },
    "Public Sanitation": {
        "toilet": 3.5,
        "urinal": 3.5,
        "restroom": 3.5,
        "washroom": 3.0,
        "sanitation": 3.0,
        "hygiene": 2.5,
        "defecation": 3.5,
        "stench": 2.5,
        "foul smell": 3.0,
        "odor": 2.0,
        "smell": 1.5,
        "unhygienic": 3.0,
        "public toilet": 4.0,
        "cleanliness": 2.0,
        "sanitary": 2.5,
    },
    "Other": {
        "encroachment": 3.0,
        "illegal": 2.0,
        "vendor": 2.0,
        "stray animal": 3.0,
        "stray dog": 3.5,
        "noise": 2.5,
        "pollution": 2.5,
        "park": 2.0,
        "bench": 2.0,
        "tree fallen": 3.5,
        "fallen tree": 3.5,
        "general": 1.5,
    },
}


def _tokenize(text: str) -> List[str]:
    """Cleans and extracts single words from text."""
    clean = re.sub(r"[^\w\s]", " ", text.lower())
    return [w for w in clean.split() if len(w) > 1]


def _extract_ngrams(words: List[str], n: int = 2) -> List[str]:
    """Generates bi-grams from normalized words."""
    return [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]


def classify_complaint(
    title: str,
    description: str,
) -> Tuple[str, float, Dict[str, float]]:
    """
    Classifies a civic complaint based on its title and description.

    Methodology:
    - Combines title (weighted 2x) and description.
    - Scans unigrams and bigrams against domain-specific keyword profiles.
    - Computes category relevance scores.
    - Applies normalized softmax probability distribution to yield a confidence
      score strictly between 0.0 and 1.0.

    Returns:
        (predicted_category, confidence_score, all_category_scores)
    """
    combined_title = title.strip() if title else ""
    combined_desc = description.strip() if description else ""

    if not combined_title and not combined_desc:
        return "Other", 0.20, {cat: (1.0 / len(CATEGORIES)) for cat in CATEGORIES}

    # Weight title higher than description
    title_words = _tokenize(combined_title)
    desc_words = _tokenize(combined_desc)

    title_bigrams = _extract_ngrams(title_words, 2)
    desc_bigrams = _extract_ngrams(desc_words, 2)

    raw_scores: Dict[str, float] = {cat: 0.0 for cat in CATEGORIES}

    for cat, profile in CATEGORY_KEYWORD_PROFILES.items():
        score = 0.0

        # Title matches (multiplier 2.2x)
        for w in title_words:
            if w in profile:
                score += profile[w] * 2.2
        for bg in title_bigrams:
            if bg in profile:
                score += profile[bg] * 2.8

        # Description matches (multiplier 1.0x)
        for w in desc_words:
            if w in profile:
                score += profile[w] * 1.0
        for bg in desc_bigrams:
            if bg in profile:
                score += profile[bg] * 1.5

        raw_scores[cat] = score

    total_score = sum(raw_scores.values())

    # If no distinctive keywords matched, default gracefully to 'Other'
    if total_score <= 0.01:
        base_confidence = 0.30
        uniform_scores = {cat: 0.10 for cat in CATEGORIES}
        uniform_scores["Other"] = base_confidence
        return "Other", base_confidence, uniform_scores

    # Softmax-style scaling for normalized probabilities
    # Temperature parameter controls sharpness
    temperature = 2.5
    max_raw = max(raw_scores.values())
    exp_scores = {cat: math.exp((s - max_raw) / temperature) for cat, s in raw_scores.items()}
    exp_sum = sum(exp_scores.values())
    normalized_probs = {cat: round(exp_s / exp_sum, 3) for cat, exp_s in exp_scores.items()}

    # Determine highest scoring category
    best_category = max(raw_scores, key=lambda k: raw_scores[k])
    best_confidence = normalized_probs[best_category]

    # Ensure confidence stays comfortably within [0.0, 1.0]
    best_confidence = max(0.25, min(0.98, best_confidence))

    return best_category, round(best_confidence, 2), normalized_probs

