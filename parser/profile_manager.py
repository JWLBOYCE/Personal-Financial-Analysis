"""Manage saved CSV import profiles."""

from __future__ import annotations

import json
import os
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROFILE_PATH = os.path.join(BASE_DIR, "config", "import_profiles.json")


def load_profiles() -> Dict[str, Dict[str, str]]:
    """Load saved import profiles from disk."""
    if not os.path.exists(PROFILE_PATH):
        return {}
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}


def save_profiles(profiles: Dict[str, Dict[str, str]]) -> None:
    """Persist profiles to disk."""
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=4)


def match_profile(
    headers: List[str],
    profiles: Dict[str, Dict[str, str]],
    threshold: float = 0.85,
) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
    """Return the best matching profile mapping for the given headers."""
    headers_lower = [h.lower() for h in headers]
    header_str = " ".join(sorted(headers_lower))
    best_score = 0.0
    best_name = None
    best_map: Optional[Dict[str, str]] = None
    for name, mapping in profiles.items():
        profile_headers = " ".join(sorted(h.lower() for h in mapping.keys()))
        score = SequenceMatcher(None, header_str, profile_headers).ratio()
        if score > best_score:
            best_score = score
            best_name = name
            best_map = mapping
    if best_score >= threshold and best_map:
        return best_name, {v: h.lower() for h, v in best_map.items()}
    return None, None


def add_profile(name: str, headers: List[str], mapping: Dict[str, str]) -> None:
    """Save a mapping for a new or existing profile."""
    profiles = load_profiles()
    profile_mapping: Dict[str, str] = {}
    for std_key, header_lower in mapping.items():
        for h in headers:
            if h.lower() == header_lower:
                profile_mapping[h] = std_key
                break
    profiles[name] = profile_mapping
    save_profiles(profiles)


__all__ = [
    "load_profiles",
    "save_profiles",
    "match_profile",
    "add_profile",
]
