import os
import argparse
import sys
import logging
from pathlib import Path
from config import settings
from scheduler.task_scheduler import PipelineScheduler
from database.search_index import SearchIndexer

# Ensure project root is on path
sys.path.append(str(Path(__file__).resolve().parent))

# Reconfigure stdout to use UTF-8 on consoles that support it
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def setup_logging():
    """Sets up console and file logging."""
    log_dir = Path(settings.BASE_DIR) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = settings.DEFAULT_LOG_PATH

    # Formatting
    log_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler (Sleek terminal output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)

    # File Handler (Detailed history)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)

    # Setup Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Clean up third-party verbose logs
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)

def run_scheduler_daemon(scheduler: PipelineScheduler, mode: str):
    """Simulates a scheduler execution run."""
    print(f"\n[Scheduler] Running Scheduled Job: [Mode: {mode.upper()}]")
    if mode == "daily":
        print("-> Running daily task: crawling and generating 10 new problems...")
        scheduler.run_crawler_pipeline()
        count = scheduler.run_generation_pipeline(count=10)
        print(f"-> Daily job finished. Inserted {count} problems.")
    elif mode == "weekly":
        print("-> Running weekly task: crawling and generating 50 new problems...")
        scheduler.run_crawler_pipeline()
        count = scheduler.run_generation_pipeline(count=50)
        print(f"-> Weekly job finished. Inserted {count} problems.")
    else:
        print("-> Run manual generation cycle...")
        count = scheduler.run_generation_pipeline(count=1)
        print(f"-> Manual job finished. Inserted {count} problems.")

    # Reindex after run
    problems = scheduler.db.list_all_problems()
    indexer = SearchIndexer()
    indexer.rebuild_index(problems)

def main():
    setup_logging()
    logger = logging.getLogger("ProblemEngine.CLI")
    
    parser = argparse.ArgumentParser(
        description="LearnLoom AI Coding Problem Generation Engine CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # 1. Crawl command
    subparsers.add_parser("crawl", help="Crawl permitted metadata concepts and save to JSON")

    # 2. Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate original coding problems using Gemini")
    gen_parser.add_argument("--count", type=int, default=1, help="Number of questions to generate successfully")

    # 3. Reindex command
    subparsers.add_parser("reindex", help="Rebuild the inverted search index")

    # 4. List command
    subparsers.add_parser("list", help="List all generated problems in the database")

    # 5. Search command
    search_parser = subparsers.add_parser("search", help="Query the local inverted search index")
    search_parser.add_argument("query", type=str, help="Search terms")

    # 6. Schedule command
    sched_parser = subparsers.add_parser("schedule", help="Simulate a scheduled job run")
    sched_parser.add_argument("--mode", choices=["daily", "weekly", "manual"], default="manual", help="Scheduled mode")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    scheduler = PipelineScheduler()

    if args.command == "crawl":
        print("[Crawler] Starting crawler...")
        saved = scheduler.run_crawler_pipeline()
        print(f"Crawler complete. Collected {saved} concepts.")
        
    elif args.command == "generate":
        print(f"[AI Generator] Starting generation engine for {args.count} problem(s)...")
        generated = scheduler.run_generation_pipeline(args.count)
        print(f"Generation cycle completed. Successfully generated & validated: {generated} problem(s).")
        
        # Proactively rebuild search index
        problems = scheduler.db.list_all_problems()
        indexer = SearchIndexer()
        indexer.rebuild_index(problems)

    elif args.command == "reindex":
        problems = scheduler.db.list_all_problems()
        indexer = SearchIndexer()
        indexer.rebuild_index(problems)
        print("[Search] Search index rebuilt successfully.")

    elif args.command == "list":
        problems = scheduler.db.list_all_problems()
        print(f"\n[DB] Total Problems in DB: {len(problems)}")
        print("--------------------------------------------------------------------------------")
        print(f"{'ID':<10} | {'Title':<30} | {'Difficulty':<10} | {'Topic':<20}")
        print("--------------------------------------------------------------------------------")
        for p in problems:
            print(f"{p.get('id'):<10} | {p.get('title')[:28]:<30} | {p.get('difficulty'):<10} | {p.get('topic')[:18]:<20}")
        print("--------------------------------------------------------------------------------")

    elif args.command == "search":
        print(f"[Search] Querying index for: '{args.query}'...")
        indexer = SearchIndexer()
        results = indexer.query_index(args.query)
        print(f"Found {len(results)} matches:\n")
        for r in results:
            print(f"[{r.get('id')}] {r.get('title')} ({r.get('difficulty')}, {r.get('xp')} XP)")
            print(f"  Topic: {r.get('topic')}")
            print(f"  Tags: {', '.join(r.get('tags'))}")
            print(f"  Complexity: {r.get('time_complexity')} | {r.get('space_complexity')}\n")

    elif args.command == "schedule":
        run_scheduler_daemon(scheduler, args.mode)

if __name__ == "__main__":
    main()

