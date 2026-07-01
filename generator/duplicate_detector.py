import logging
from difflib import SequenceMatcher
import re

logger = logging.getLogger("ProblemEngine.DuplicateDetector")

class DuplicateDetector:
    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold

    def _normalize_text(self, text: str) -> str:
        """Helper to lowercase and clean text strings."""
        if not text:
            return ""
        text = text.lower().strip()
        # Remove special characters/punctuation
        text = re.sub(r"[^\w\s]", "", text)
        return text

    def _jaccard_similarity(self, list1: list, list2: list) -> float:
        """Compute Jaccard similarity between two lists/sets."""
        set1 = set([str(x).lower().strip() for x in list1 if x])
        set2 = set([str(x).lower().strip() for x in list2 if x])
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        return len(set1.intersection(set2)) / len(set1.union(set2))

    def _sequence_similarity(self, str1: str, str2: str) -> float:
        """Compute string similarity using SequenceMatcher (Levenshtein-like)."""
        s1 = self._normalize_text(str1)
        s2 = self._normalize_text(str2)
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        return SequenceMatcher(None, s1, s2).ratio()

    def check_similarity(self, new_problem: dict, existing_problem: dict) -> dict:
        """
        Compare new_problem against existing_problem.
        Returns a dict containing similarities and whether it is a duplicate.
        """
        title_sim = self._sequence_similarity(
            new_problem.get("title", ""), 
            existing_problem.get("title", "")
        )
        statement_sim = self._sequence_similarity(
            new_problem.get("statement", ""), 
            existing_problem.get("statement", "")
        )
        tag_sim = self._jaccard_similarity(
            new_problem.get("tags", []), 
            existing_problem.get("tags", [])
        )

        # Weighted score: 40% Title, 50% Statement, 10% Tags
        weighted_score = (title_sim * 0.4) + (statement_sim * 0.5) + (tag_sim * 0.1)

        is_duplicate = (
            title_sim >= self.threshold or 
            statement_sim >= self.threshold or 
            weighted_score >= self.threshold
        )

        return {
            "title_similarity": title_sim,
            "statement_similarity": statement_sim,
            "tag_similarity": tag_sim,
            "weighted_similarity": weighted_score,
            "is_duplicate": is_duplicate
        }

    def check_against_all(self, new_problem: dict, existing_problems: list) -> tuple:
        """
        Compares the candidate problem against a list of existing problems.
        Returns (is_duplicate, duplicate_details).
        """
        for idx, existing in enumerate(existing_problems):
            result = self.check_similarity(new_problem, existing)
            if result["is_duplicate"]:
                logger.warning(
                    f"Duplicate detected with problem index {idx} (Title: '{existing.get('title')}'). "
                    f"Weighted similarity: {result['weighted_similarity']:.2f}"
                )
                return True, result
        return False, None
