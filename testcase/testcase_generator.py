import json
import logging
from pathlib import Path
import google.generativeai as genai
from config import settings

logger = logging.getLogger("ProblemEngine.TestcaseGenerator")

class TestcaseGenerator:
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

    def generate_testcases(self, problem: dict) -> dict:
        """
        Generates public and hidden test cases.
        """
        if not self.has_api:
            return self._generate_mock_testcases(problem)

        try:
            template = self._load_prompt("testcase_prompt.txt")
            prompt = template.format(
                title=problem.get("title", ""),
                statement=problem.get("statement", ""),
                constraints=", ".join(problem.get("constraints", [])),
                input_format=problem.get("input_format", ""),
                output_format=problem.get("output_format", "")
            )

            logger.info("Querying Gemini to generate test cases...")
            response = self.model.generate_content(prompt)
            cleaned_text = self._clean_json_response(response.text)
            
            return json.loads(cleaned_text)
        except Exception as e:
            logger.error(f"Error generating test cases: {e}. Using mock cases.")
            return self._generate_mock_testcases(problem)

    def _generate_mock_testcases(self, problem: dict) -> dict:
        """Generates standard public and hidden test cases matching mock problem constraints."""
        # 3 Public cases
        public_cases = [
            {"input": "5\n1 2 3 4 5", "output": "2"},
            {"input": "3\n10 10 10", "output": "1"},
            {"input": "4\n1 5 10 20", "output": "-1"}
        ]
        
        # 10 Hidden cases (edges, large, random)
        hidden_cases = [
            # Edge cases (N = 1, single element)
            {"input": "1\n50", "output": "1", "type": "edge"},
            {"input": "1\n1000", "output": "1", "type": "edge"},
            {"input": "2\n1 1", "output": "1", "type": "edge"},
            
            # Random cases
            {"input": "6\n2 4 6 8 10 12", "output": "2", "type": "random"},
            {"input": "5\n5 12 18 20 25", "output": "3", "type": "random"},
            {"input": "7\n1 2 5 2 1 2 5", "output": "2", "type": "random"},
            {"input": "8\n100 200 150 120 180 220 200 190", "output": "3", "type": "random"},
            
            # Large input cases
            {"input": "10\n" + " ".join([str(i) for i in range(1, 11)]), "output": "2", "type": "large"},
            {"input": "20\n" + " ".join([str(i*2) for i in range(1, 21)]), "output": "2", "type": "large"},
            {"input": "50\n" + " ".join(["500"] * 50), "output": "1", "type": "large"}
        ]
        
        return {
            "public": public_cases,
            "hidden": hidden_cases
        }
