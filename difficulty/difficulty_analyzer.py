import logging
import re

logger = logging.getLogger("ProblemEngine.DifficultyAnalyzer")

class DifficultyAnalyzer:
    def __init__(self):
        pass

    def analyze_difficulty(self, problem: dict, editorial: dict = None) -> str:
        """
        Calculates a complexity score and maps it to Easy, Medium, or Hard.
        Score range: 0-100.
        - Easy: 0 - 35
        - Medium: 36 - 70
        - Hard: 71 - 100
        """
        score = 0
        
        # 1. Analyze Constraints
        constraints = problem.get("constraints", [])
        constraint_str = " ".join(constraints).lower()
        
        # Look for numbers like 10^5, 10^6, 2 * 10^5, etc.
        large_constraints = False
        if "10^5" in constraint_str or "10^6" in constraint_str or "200000" in constraint_str:
            score += 25
            large_constraints = True
        elif "10^7" in constraint_str or "10^8" in constraint_str or "10^9" in constraint_str:
            score += 35
            large_constraints = True
        else:
            score += 10 # Low constraints

        # 2. Analyze Algorithms and Tags
        tags = [t.lower() for t in problem.get("tags", [])]
        topic = problem.get("topic", "").lower()
        
        hard_topics = {"dynamic programming", "segment tree", "fenwick tree", "graph", "dijkstra", "strongly connected components", "trie", "suffix array"}
        medium_topics = {"binary search", "sliding window", "two pointers", "bfs", "dfs", "greedy", "heap", "priority queue", "recursion"}
        
        has_hard = False
        has_medium = False
        
        for t in tags + [topic]:
            if any(h in t for h in hard_topics):
                has_hard = True
            elif any(m in t for m in medium_topics):
                has_medium = True

        if has_hard:
            score += 30
        elif has_medium:
            score += 15
        else:
            score += 5

        # 3. Analyze Time Complexity from Editorial (if available)
        time_comp = ""
        if editorial:
            time_comp = editorial.get("time_complexity", "").lower()
        
        if "o(n log n)" in time_comp or "o(log n)" in time_comp:
            score += 15
        elif "o(n)" in time_comp:
            score += 10
        elif "o(2^" in time_comp or "o(n!)" in time_comp or "exponential" in time_comp:
            score += 25
        elif "o(n^2)" in time_comp:
            score += 10 if large_constraints else 5

        # 4. AI suggested difficulty (Initial input)
        ai_difficulty = problem.get("difficulty", "Medium").lower()
        if ai_difficulty == "hard":
            score += 10
        elif ai_difficulty == "medium":
            score += 5
        
        # Calculate final mapping
        difficulty_class = "Medium"
        if score <= 35:
            difficulty_class = "Easy"
        elif score >= 71:
            difficulty_class = "Hard"
        else:
            difficulty_class = "Medium"

        logger.info(f"Analyzed difficulty: Score={score}, Class={difficulty_class} (AI suggested: {ai_difficulty.capitalize()})")
        return difficulty_class
