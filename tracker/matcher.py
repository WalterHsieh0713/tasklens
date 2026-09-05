"""Fuzzy-matches on-screen text (window title + OCR'd screen text) against the task list.
No LLM/API key needed -- just string similarity, which is enough to catch "Chapter 4 Notes -
Google Docs" as a match for a "Read Chapter 4" task even with extra noise around it.
"""
from rapidfuzz import fuzz

MATCH_THRESHOLD = 82


def best_match(haystack: str, tasks: list[dict]) -> tuple[dict | None, int]:
    """Returns the task whose title best matches the given text, and the match score."""
    haystack_lower = haystack.lower()
    best_task = None
    best_score = 0
    for task in tasks:
        if task["status"] == "done":
            continue
        needle = task["title"].lower()
        score = fuzz.partial_ratio(needle, haystack_lower)
        if score > best_score:
            best_score = score
            best_task = task
    if best_score >= MATCH_THRESHOLD:
        return best_task, best_score
    return None, best_score
