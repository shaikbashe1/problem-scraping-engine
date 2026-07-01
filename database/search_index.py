import logging
import json
import re
from pathlib import Path

logger = logging.getLogger("ProblemEngine.SearchIndexer")

class SearchIndexer:
    def __init__(self, index_path: Path = None):
        if index_path:
            self.index_path = Path(index_path)
        else:
            self.index_path = Path(__file__).resolve().parent / "search_index.json"

    def _normalize_word(self, word: str) -> str:
        return re.sub(r"[^\w]", "", word.lower().strip())

    def rebuild_index(self, problems: list):
        """
        Rebuilds the search index from scratch using all problems in the database.
        Each word mapping points to problem IDs matching the query.
        """
        logger.info(f"Rebuilding search index for {len(problems)} problems...")
        index = {
            "keywords": {},     # keyword -> list of problem IDs
            "problems": {}      # problem ID -> fast metadata lookup (Title, Tags, Difficulty, XP)
        }

        for p in problems:
            pid = p.get("id")
            title = p.get("title", "")
            tags = p.get("tags", [])
            diff = p.get("difficulty", "")
            topic = p.get("topic", "")
            xp = str(p.get("xp", 0))
            
            # Extract time/space complexities from editorial
            editorial = p.get("editorial", {})
            time_comp = editorial.get("time_complexity", "")
            space_comp = editorial.get("space_complexity", "")

            # Build fast lookup summary
            index["problems"][pid] = {
                "title": title,
                "difficulty": diff,
                "tags": tags,
                "topic": topic,
                "xp": p.get("xp", 0),
                "time_complexity": time_comp,
                "space_complexity": space_comp
            }

            # Collect terms for index
            search_terms = set()
            
            # Add titles split into words
            for word in title.split():
                search_terms.add(self._normalize_word(word))
                
            # Add topic split into words
            for word in topic.split():
                search_terms.add(self._normalize_word(word))

            # Add tags
            for tag in tags:
                search_terms.add(self._normalize_word(tag))

            # Add difficulty, XP, and complexity terms
            search_terms.add(self._normalize_word(diff))
            search_terms.add(self._normalize_word(xp))
            search_terms.add(self._normalize_word(time_comp))
            search_terms.add(self._normalize_word(space_comp))

            # Register keyword links
            for term in search_terms:
                if not term or len(term) < 2:
                    continue
                if term not in index["keywords"]:
                    index["keywords"][term] = []
                if pid not in index["keywords"][term]:
                    index["keywords"][term].append(pid)

        # Write to disk
        try:
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=4)
            logger.info(f"Search index written successfully to {self.index_path}.")
        except Exception as e:
            logger.error(f"Failed to write search index: {e}")

    def query_index(self, query: str) -> list:
        """Searches the inverted index and returns matching problem objects."""
        if not self.index_path.exists():
            return []

        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                index = json.load(f)
        except Exception:
            return []

        words = [self._normalize_word(w) for w in query.split() if self._normalize_word(w)]
        if not words:
            return []

        matched_ids = None
        for word in words:
            # Find closest matches or exact match in keywords list
            word_matches = set()
            for key, pids in index.get("keywords", {}).items():
                if word in key:
                    word_matches.update(pids)
            
            if matched_ids is None:
                matched_ids = word_matches
            else:
                matched_ids = matched_ids.intersection(word_matches)

        if not matched_ids:
            return []

        results = []
        for pid in matched_ids:
            if pid in index.get("problems", {}):
                item = index["problems"][pid]
                item["id"] = pid
                results.append(item)

        return results
