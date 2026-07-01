import sys
import logging
from pathlib import Path
import json

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

from crawler.metadata_crawler import MetadataCrawler
from generator.duplicate_detector import DuplicateDetector
from generator.problem_generator import ProblemGenerator
from starter_code.starter_generator import StarterGenerator
from testcase.testcase_generator import TestcaseGenerator
from editorial.editorial_generator import EditorialGenerator
from difficulty.difficulty_analyzer import DifficultyAnalyzer
from validator.code_validator import CodeValidator
from database.supabase_client import SupabaseDatabase
from database.search_index import SearchIndexer
from config import settings

def run_diagnostics():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("ProblemEngine.Diagnostics")
    logger.info("=== STARTING DIAGNOSTICS FOR LEARNLOOM AI PROBLEM ENGINE ===")

    # 1. Test Crawler
    logger.info("[Test 1] Testing Metadata Crawler...")
    crawler = MetadataCrawler(settings.METADATA_DIR)
    crawled_count = crawler.crawl_permitted_sources()
    logger.info(f"-> Crawler Success: Created {crawled_count} metadata files in {settings.METADATA_DIR}")
    assert crawled_count > 0, "Crawler did not save any files"

    # 2. Test Duplicate Detector
    logger.info("[Test 2] Testing Duplicate Detector...")
    detector = DuplicateDetector(settings.SIMILARITY_THRESHOLD)
    prob_a = {"title": "Two Pointer Sum Target", "statement": "Find a target sum in array.", "tags": ["array"]}
    prob_b = {"title": "Two Pointer Sum Target Variant", "statement": "Find a target sum in an array using pointers.", "tags": ["array"]}
    res = detector.check_similarity(prob_a, prob_b)
    logger.info(f"-> Similarity Score: {res['weighted_similarity']:.2f}. Duplicate detected: {res['is_duplicate']}")
    
    # Check that identical items are detected
    res_identical = detector.check_similarity(prob_a, prob_a)
    assert res_identical["is_duplicate"] == True, "Identical problems must be marked as duplicate"
    logger.info("-> Duplicate Detector tests passed.")

    # 3. Test Generator & Components (Running Mock Mode to verify integrity offline)
    logger.info("[Test 3] Testing AI Problem Generator & Code Boilerplates...")
    generator = ProblemGenerator()
    test_meta = {
        "topic": "Sliding Window",
        "difficulty": "Medium",
        "tags": ["Array"],
        "concept": "Variable Window",
        "learning_objective": "Dynamic range size calculations"
    }
    
    problem = generator.generate_problem(test_meta)
    logger.info(f"-> Generated Problem Title: '{problem.get('title')}'")
    assert problem.get("title"), "Problem title cannot be empty"
    
    # 4. Boilerplates
    starter_gen = StarterGenerator(generator)
    starters = starter_gen.generate_starter_code(problem)
    assert "python" in starters and "java" in starters, "Starter templates missing languages"
    logger.info("-> Starter templates generated for Java, Python, C, C++, JavaScript.")

    # 5. Test Cases
    testcase_gen = TestcaseGenerator(generator)
    cases = testcase_gen.generate_testcases(problem)
    assert len(cases.get("public", [])) > 0, "Public cases missing"
    assert len(cases.get("hidden", [])) >= 10, "Hidden cases missing minimum length of 10"
    logger.info(f"-> Test cases generated successfully ({len(cases.get('public'))} public, {len(cases.get('hidden'))} hidden).")

    # 6. Editorial & Hints
    editorial_gen = EditorialGenerator(generator)
    editorial = editorial_gen.generate_editorial(problem)
    assert editorial.get("optimal"), "Optimal approach explanation missing"
    
    hint_gen = generator # HintGenerator reuse
    from generator.hint_generator import HintGenerator
    hint_gen = HintGenerator(generator)
    hints = hint_gen.generate_hints(problem)
    assert len(hints.get("hints", [])) == 3, "Hints count must be exactly 3"
    logger.info("-> Editorial and 3 progressive hints generated successfully.")

    # 7. Difficulty Analyzer
    logger.info("[Test 4] Testing Difficulty Analyzer...")
    analyzer = DifficultyAnalyzer()
    calculated_diff = analyzer.analyze_difficulty(problem, editorial)
    logger.info(f"-> Calculated Difficulty Class: {calculated_diff}")
    problem["difficulty"] = calculated_diff

    # 8. Validator Execution
    logger.info("[Test 5] Running Code Validator (local compilation & test case runs)...")
    validator = CodeValidator(generator)
    val_success = validator.validate_problem(problem, cases, starters)
    logger.info(f"-> Validator success status: {val_success}")
    assert val_success == True, "Local execution validation failed"

    # 9. Database insertion
    logger.info("[Test 6] Running DB integration test...")
    db = SupabaseDatabase()
    problem_id = db.insert_problem(problem, cases, hints, editorial, starters)
    logger.info(f"-> Inserted problem record. Generated ID: {problem_id}")
    assert problem_id.startswith("LL-"), "Generated ID must follow LL-000000 format"

    # 10. Search indexing
    logger.info("[Test 7] Testing Search Indexer...")
    indexer = SearchIndexer()
    problems_list = db.list_all_problems()
    indexer.rebuild_index(problems_list)
    
    search_query = "sliding"
    matches = indexer.query_index(search_query)
    logger.info(f"-> Query '{search_query}' matched: {[m.get('title') for m in matches]}")
    assert len(matches) > 0, f"Search index query for '{search_query}' failed to match generated problem"

    logger.info("=== DIAGNOSTICS COMPLETE. ALL PIPELINE SYSTEMS NOMINAL! ===")

if __name__ == "__main__":
    run_diagnostics()
