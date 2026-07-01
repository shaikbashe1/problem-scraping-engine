import json
import logging
from pathlib import Path
import google.generativeai as genai
from config import settings

logger = logging.getLogger("ProblemEngine.StarterGenerator")

class StarterGenerator:
    def __init__(self, generator_instance=None):
        # We can reuse the API state from the main generator
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

    def generate_starter_code(self, problem: dict) -> dict:
        """
        Generates structured starter code templates.
        """
        if not self.has_api:
            return self._generate_mock_starter(problem)

        try:
            template = self._load_prompt("starter_prompt.txt")
            prompt = template.format(
                title=problem.get("title", ""),
                statement=problem.get("statement", ""),
                input_format=problem.get("input_format", ""),
                output_format=problem.get("output_format", ""),
                constraints=", ".join(problem.get("constraints", []))
            )

            logger.info("Querying Gemini to generate starter code templates...")
            response = self.model.generate_content(prompt)
            cleaned_text = self._clean_json_response(response.text)
            
            return json.loads(cleaned_text)
        except Exception as e:
            logger.error(f"Error generating starter code: {e}. Falling back to mock templates.")
            return self._generate_mock_starter(problem)

    def _generate_mock_starter(self, problem: dict) -> dict:
        """Generates standard programming language skeleton templates."""
        return {
            "python": (
                "def solve(n: int, coordinates: list[int]) -> int:\n"
                "    # TODO: Implement original sliding window logic\n"
                "    return 0\n"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static int solve(int n, int[] coordinates) {\n"
                "        // TODO: Implement solution\n"
                "        return 0;\n"
                "    }\n"
                "}\n"
            ),
            "c": (
                "#include <stdio.h>\n\n"
                "int solve(int n, int coordinates[]) {\n"
                "    // TODO: Implement solution\n"
                "    return 0;\n"
                "}\n"
            ),
            "cpp": (
                "#include <vector>\n"
                "using namespace std;\n\n"
                "class Solution {\n"
                "public:\n"
                "    int solve(int n, vector<int>& coordinates) {\n"
                "        // TODO: Implement solution\n"
                "        return 0;\n"
                "    }\n"
                "};\n"
            ),
            "javascript": (
                "function solve(n, coordinates) {\n"
                "    // TODO: Implement solution\n"
                "    return 0;\n"
                "}\n"
            )
        }
