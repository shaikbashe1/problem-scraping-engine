import os
import time
import logging
from pathlib import Path
import random
from config import settings
from crawler.metadata_crawler import MetadataCrawler
from generator.problem_generator import ProblemGenerator
from generator.duplicate_detector import DuplicateDetector
from generator.hint_generator import HintGenerator
from starter_code.starter_generator import StarterGenerator
from testcase.testcase_generator import TestcaseGenerator
from editorial.editorial_generator import EditorialGenerator
from difficulty.difficulty_analyzer import DifficultyAnalyzer
from validator.code_validator import CodeValidator
from database.supabase_client import SupabaseDatabase

logger = logging.getLogger("ProblemEngine.Scheduler")

class PipelineScheduler:
    def __init__(self):
        self.crawler = MetadataCrawler(settings.METADATA_DIR)
        self.generator = ProblemGenerator()
        self.duplicate_detector = DuplicateDetector(settings.SIMILARITY_THRESHOLD)
        self.hint_generator = HintGenerator(self.generator)
        self.starter_generator = StarterGenerator(self.generator)
        self.testcase_generator = TestcaseGenerator(self.generator)
        self.editorial_generator = EditorialGenerator(self.generator)
        self.difficulty_analyzer = DifficultyAnalyzer()
        self.validator = CodeValidator(self.generator)
        self.db = SupabaseDatabase()

    def run_crawler_pipeline(self) -> int:
        """Runs the metadata crawler to collect concepts."""
        logger.info("Triggering crawler pipeline...")
        return self.crawler.crawl_permitted_sources()

    def run_generation_pipeline(self, count: int = 1) -> int:
        """
        Executes the AI Problem Generation pipeline for 'count' successful questions.
        Handles similarity regeneration loops and validation checks.
        """
        logger.info(f"Triggering generation pipeline for {count} questions...")
        
        # 1. Ensure we have metadata files to generate from
        metadata_files = list(settings.METADATA_DIR.glob("*.json"))
        if not metadata_files:
            logger.info("No metadata files found. Running crawler first...")
            self.run_crawler_pipeline()
            metadata_files = list(settings.METADATA_DIR.glob("*.json"))
            if not metadata_files:
                logger.error("No metadata available. Aborting pipeline.")
                return 0

        inserted_count = 0
        failed_count = 0
        duplicate_count = 0
        start_time = time.time()

        # Load existing problems from DB for similarity checking
        logger.info("Loading existing database records for similarity detection...")
        existing_problems = self.db.list_all_problems()
        logger.info(f"Loaded {len(existing_problems)} existing problems.")

        # Shuffle metadata files to ensure random generation tracks
        random.shuffle(metadata_files)

        for m_file in metadata_files:
            if inserted_count >= count:
                break

            logger.info(f"Processing metadata file: {m_file.name}")
            try:
                with open(m_file, "r", encoding="utf-8") as f:
                    meta_data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to read metadata file {m_file}: {e}")
                continue

            # Generation loop with retry capabilities
            success = False
            max_retries = 3
            for attempt in range(max_retries):
                logger.info(f"Generation attempt {attempt + 1} of {max_retries} for topic: {meta_data.get('topic')}")
                
                # 1. Generate Problem
                problem = self.generator.generate_problem(meta_data)
                
                # 2. Check duplicates against DB
                is_dup, dup_details = self.duplicate_detector.check_against_all(problem, existing_problems)
                if is_dup:
                    logger.warning("Generated problem is too similar to existing records. Regenerating...")
                    duplicate_count += 1
                    continue # Try next attempt

                # 3. Generate solutions, test cases, templates, editorials, hints
                logger.info("Generating problem components...")
                starter_code = self.starter_generator.generate_starter_code(problem)
                testcases = self.testcase_generator.generate_testcases(problem)
                editorial = self.editorial_generator.generate_editorial(problem)
                hints = self.hint_generator.generate_hints(problem)

                # 4. Analyze difficulty
                final_difficulty = self.difficulty_analyzer.analyze_difficulty(problem, editorial)
                problem["difficulty"] = final_difficulty

                # 5. Validate the whole generated payload
                is_valid = self.validator.validate_problem(problem, testcases, starter_code)
                if not is_valid:
                    logger.warning("Generated question failed validation. Regenerating...")
                    failed_count += 1
                    continue

                # 6. Insert into database
                problem_id = self.db.insert_problem(problem, testcases, hints, editorial, starter_code)
                
                # Add to existing problems list to avoid duplicate generation in the same batch
                full_inserted_record = {
                    "id": problem_id,
                    "title": problem.get("title"),
                    "statement": problem.get("statement"),
                    "tags": problem.get("tags")
                }
                existing_problems.append(full_inserted_record)
                
                inserted_count += 1
                success = True
                break # Success, break attempt retry loop

            if not success:
                logger.error(f"Failed to generate a valid unique problem for metadata: {m_file.name}")

        end_time = time.time()
        elapsed = end_time - start_time
        
        # Log Summary
        logger.info("==========================================")
        logger.info("Pipeline Generation Summary:")
        logger.info(f"Time Elapsed: {elapsed:.2f} seconds")
        logger.info(f"Successfully Inserted: {inserted_count}")
        logger.info(f"Duplicates Discarded: {duplicate_count}")
        logger.info(f"Validation Failures: {failed_count}")
        logger.info("==========================================")
        
        return inserted_count
