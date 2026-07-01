import json
import logging
from pathlib import Path
import google.generativeai as genai
from config import settings

logger = logging.getLogger("ProblemEngine.EditorialGenerator")

class EditorialGenerator:
    def __init__(self, generator_instance=None):
        self.has_api = False
        if generator_instance and hasattr(generator_instance, 'has_api'):
            self.has_api = generator_instance.has_api
            if self.has_api:
                self.model = generator_instance.model
        else:
            self.api_key = settings.GEMINI_API_KEY
            if self.api_key and "your_gemini_api_key" not in self.api_key:
                try:
                    genai.configure(api_key=self.api_key)
                    self.model = genai.GenerativeModel('gemini-1.5-flash')
                    self.has_api = True
                except Exception:
                    pass

    def _load_prompt(self, filename: str) -> str:
        prompt_path = Path(settings.PROMPTS_DIR) / filename
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _clean_json_response(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text

    def generate_editorial(self, problem: dict) -> dict:
        """
        Generates the problem editorial details.
        """
        if not self.has_api:
            return self._generate_mock_editorial(problem)

        try:
            template = self._load_prompt("editorial_prompt.txt")
            prompt = template.format(
                title=problem.get("title", ""),
                statement=problem.get("statement", ""),
                constraints=", ".join(problem.get("constraints", []))
            )

            logger.info("Querying Gemini to generate editorial...")
            response = self.model.generate_content(prompt)
            cleaned_text = self._clean_json_response(response.text)
            
            return json.loads(cleaned_text)
        except Exception as e:
            logger.error(f"Error generating editorial: {e}. Using mock editorial.")
            return self._generate_mock_editorial(problem)

    def _generate_mock_editorial(self, problem: dict) -> dict:
        """Generates standard editorial details matching mock constraints."""
        return {
            "brute_force": (
                "Iterate through all possible contiguous subarrays using a nested loop. "
                "For each subarray, calculate the min and max coordinates to check variance. "
                "Return the minimum length of subarrays satisfying the condition."
            ),
            "optimal": (
                "Use a sliding window (two pointers) approach. Maintain a sliding window [left, right]. "
                "Expand the right pointer to include elements, updating a frequency map or min/max deque. "
                "If the current window state violates safety limits, increment the left pointer to contract "
                "the window and optimize the length."
            ),
            "time_complexity": "Brute Force: O(N^2), Optimal: O(N)",
            "space_complexity": "Brute Force: O(1), Optimal: O(K) where K is the alphabet size or window element range.",
            "common_mistakes": [
                "Using a brute force O(N^2) solution which TLEs (Time Limit Exceeded) for N = 10^5.",
                "Off-by-one errors when expanding the right pointer or shrinking the left pointer.",
                "Not resetting the sliding window bounds properly when bounds become invalid."
            ]
        }
