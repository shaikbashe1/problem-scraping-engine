import os
import json
import logging
from pathlib import Path
import google.generativeai as genai
from config import settings

logger = logging.getLogger("ProblemEngine.ProblemGenerator")

class ProblemGenerator:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.has_api = False
        
        if self.api_key and "your_gemini_api_key" not in self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.has_api = True
                logger.info("Gemini API initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API: {e}")
        else:
            logger.warning("No valid GEMINI_API_KEY found. Engine will run in MOCK mode.")

    def _load_prompt(self, filename: str) -> str:
        """Loads a prompt template from the prompts folder."""
        prompt_path = Path(settings.PROMPTS_DIR) / filename
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _clean_json_response(self, text: str) -> str:
        """Removes markdown code blocks (e.g., ```json ... ```) from LLM output."""
        text = text.strip()
        if text.startswith("```"):
            # Split by lines, discard the first and last line if they contain backticks
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text

    def generate_problem(self, metadata: dict) -> dict:
        """
        Generates an original problem using Gemini based on metadata.
        Falls back to mock problem generation if API is not available.
        """
        if not self.has_api:
            return self._generate_mock_problem(metadata)

        try:
            template = self._load_prompt("problem_prompt.txt")
            prompt = template.format(
                topic=metadata.get("topic", "Coding"),
                difficulty=metadata.get("difficulty", "Medium"),
                tags=", ".join(metadata.get("tags", [])),
                concept=metadata.get("concept", "General")
            )

            logger.info(f"Querying Gemini to generate original problem for: {metadata.get('topic')}")
            response = self.model.generate_content(prompt)
            cleaned_text = self._clean_json_response(response.text)
            
            problem_data = json.loads(cleaned_text)
            # Add metadata keys to the output structure
            problem_data["topic"] = metadata.get("topic")
            problem_data["tags"] = metadata.get("tags")
            problem_data["concept"] = metadata.get("concept")
            problem_data["learning_objective"] = metadata.get("learning_objective", "")
            problem_data["difficulty"] = metadata.get("difficulty")
            
            return problem_data
        except Exception as e:
            logger.error(f"Error generating problem via Gemini: {e}. Falling back to mock.")
            return self._generate_mock_problem(metadata)

    def _generate_mock_problem(self, metadata: dict) -> dict:
        """Generates a high-quality mock original problem for offline validation."""
        topic = metadata.get("topic", "Sliding Window")
        concept = metadata.get("concept", "Variable Window")
        difficulty = metadata.get("difficulty", "Medium")
        tags = metadata.get("tags", ["Array"])
        learning_obj = metadata.get("learning_objective", "Optimize range analysis")

        # Create structured problem payload
        title = f"Original AI {topic} Challenge"
        statement = (
            f"Given an array of integers representing the sensor log of a space vessel, "
            f"find the minimum contiguous subsegment where the variance of coordinates is within safety limits. "
            f"This challenge focuses on the concept of {concept} with {difficulty} difficulty."
        )
        constraints = [
            "1 <= N <= 10^5",
            "1 <= coordinates[i] <= 1000"
        ]
        input_format = "An integer N followed by N integers representing the array coordinates."
        output_format = "An integer representing the length of the minimum subsegment, or -1 if no such segment exists."
        examples = [
            {
                "input": "5\n1 2 3 4 5",
                "output": "2",
                "explanation": "Subsegment [2, 3] satisfies the constraint under safety variance limits."
            }
        ]

        return {
            "title": title,
            "statement": statement,
            "constraints": constraints,
            "input_format": input_format,
            "output_format": output_format,
            "examples": examples,
            "topic": topic,
            "concept": concept,
            "difficulty": difficulty,
            "tags": tags,
            "learning_objective": learning_obj
        }
