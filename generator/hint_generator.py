import json
import logging
from pathlib import Path
import google.generativeai as genai
from config import settings

logger = logging.getLogger("ProblemEngine.HintGenerator")

class HintGenerator:
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

    def generate_hints(self, problem: dict) -> dict:
        """
        Generates 3 progressive hints.
        """
        if not self.has_api:
            return self._generate_mock_hints(problem)

        try:
            template = self._load_prompt("hints_prompt.txt")
            prompt = template.format(
                title=problem.get("title", ""),
                statement=problem.get("statement", ""),
                constraints=", ".join(problem.get("constraints", []))
            )

            logger.info("Querying Gemini to generate hints...")
            response = self.model.generate_content(prompt)
            cleaned_text = self._clean_json_response(response.text)
            
            return json.loads(cleaned_text)
        except Exception as e:
            logger.error(f"Error generating hints: {e}. Using mock hints.")
            return self._generate_mock_hints(problem)

    def _generate_mock_hints(self, problem: dict) -> dict:
        """Generates standard progressive hints matching mock constraints."""
        return {
            "hints": [
                "Think about how the constraints change as you expand your search area. Can you reuse results from a smaller range?",
                "Use a sliding window. Try moving the right pointer to expand and the left pointer to contract elements.",
                "To optimize, keep track of elements using a map or a monotonic structure to perform updates in constant time O(1)."
            ]
        }
