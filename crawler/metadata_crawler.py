import os
import json
import logging
from pathlib import Path
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("ProblemEngine.Crawler")

# Predefined high-quality metadata maps representing standard learning tracks (fallback/offline)
DSA_TOPIC_TEMPLATES = [
    {"topic": "Sliding Window", "difficulty": "Medium", "tags": ["Array", "Two Pointer"], "concept": "Variable Window Size", "learning_objective": "Optimize subsegment tracking dynamically"},
    {"topic": "Sliding Window", "difficulty": "Easy", "tags": ["Array", "String"], "concept": "Fixed Window Size", "learning_objective": "Maintain cumulative state in linear time"},
    {"topic": "Two Pointers", "difficulty": "Easy", "tags": ["Array", "Two Pointer"], "concept": "Opposite ends convergence", "learning_objective": "Find pairs satisfying sorting bounds"},
    {"topic": "Two Pointers", "difficulty": "Medium", "tags": ["Array", "Sorting"], "concept": "Fast and slow pointer", "learning_objective": "Detect cycle patterns in list structures"},
    {"topic": "Binary Search", "difficulty": "Medium", "tags": ["Array", "Binary Search"], "concept": "Search space reduction", "learning_objective": "Perform binary search on answer range"},
    {"topic": "Binary Search", "difficulty": "Hard", "tags": ["Array", "Optimization"], "concept": "Maximize minimum distance", "learning_objective": "Find optimal threshold in structured intervals"},
    {"topic": "Prefix Sum", "difficulty": "Easy", "tags": ["Array", "Prefix Sum"], "concept": "Range query indexing", "learning_objective": "Perform dynamic constant-time sum queries"},
    {"topic": "Breadth First Search", "difficulty": "Medium", "tags": ["Graph", "BFS"], "concept": "Shortest path in unweighted graph", "learning_objective": "Explore layer-by-layer traversal"},
    {"topic": "Depth First Search", "difficulty": "Medium", "tags": ["Graph", "DFS", "Tree"], "concept": "Backtracking search", "learning_objective": "Explore recursive path traversal"},
    {"topic": "Dynamic Programming", "difficulty": "Medium", "tags": ["Dynamic Programming", "Memoization"], "concept": "1D State Transition", "learning_objective": "Optimize recursive subproblems"},
    {"topic": "Dynamic Programming", "difficulty": "Hard", "tags": ["Dynamic Programming", "Grid"], "concept": "2D Grid Path optimization", "learning_objective": "Minimize path cost on state grids"},
    {"topic": "Heaps & Priority Queues", "difficulty": "Medium", "tags": ["Heap", "Priority Queue"], "concept": "K-way Merge", "learning_objective": "Maintain ordered elements in dynamic collections"},
    {"topic": "Monotonic Stack", "difficulty": "Medium", "tags": ["Stack", "Monotonic Stack"], "concept": "Next Greater Element", "learning_objective": "Track previous or next optimal indexes in linear time"},
]

class MetadataCrawler:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def crawl_permitted_sources(self) -> int:
        """
        Crawls public directories or algorithms indices (like Wikipedia's list of algorithms or GitHub DSA roadmaps)
        to extract topics, then merges them with baseline topics to build the metadata collection.
        Returns the number of saved metadata files.
        """
        logger.info("Starting metadata crawler...")
        crawled_topics = []

        try:
            # Scrape public Wikipedia or generic algorithm index pages (Safe & permitted metadata)
            url = "https://en.wikipedia.org/wiki/List_of_algorithms"
            headers = {"User-Agent": "LearnLoomCrawler/1.0"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Find headings or links that list algorithm subcategories
                links = soup.select("div.mw-parser-output ul li a")
                for link in links[:30]:  # Limit to first 30 for safety and rate-limit friendliness
                    text = link.get_text().strip()
                    if text and len(text) < 40 and "algorithm" in text.lower():
                        crawled_topics.append(text)
                logger.info(f"Crawled {len(crawled_topics)} algorithm references from public domains.")
        except Exception as e:
            logger.warning(f"Failed to crawl online source (using baseline templates instead): {e}")

        # Combine with our baseline templates to expand coverage
        saved_count = 0
        
        # Populate files
        for idx, template in enumerate(DSA_TOPIC_TEMPLATES):
            # Write to output folder
            file_name = f"metadata_baseline_{idx + 1:04d}.json"
            file_path = self.output_dir / file_name
            with open(file_path, "w") as f:
                json.dump(template, f, indent=4)
            saved_count += 1

        # Integrate online crawled topics
        for idx, topic in enumerate(crawled_topics):
            # Formulate metadata from crawled data
            difficulty = "Medium" if idx % 2 == 0 else "Hard"
            metadata = {
                "topic": topic,
                "difficulty": difficulty,
                "tags": [topic.split()[0], "Algorithm"] if len(topic.split()) > 0 else ["Algorithm"],
                "concept": topic,
                "learning_objective": f"Understand the core properties and runtime behavior of {topic}."
            }
            file_name = f"metadata_crawled_{idx + 1:04d}.json"
            file_path = self.output_dir / file_name
            with open(file_path, "w") as f:
                json.dump(metadata, f, indent=4)
            saved_count += 1

        logger.info(f"Metadata crawler complete. Saved {saved_count} items to {self.output_dir}.")
        return saved_count

if __name__ == "__main__":
    # Test crawler directly
    logging.basicConfig(level=logging.INFO)
    crawler = MetadataCrawler(Path("../metadata"))
    crawler.crawl_permitted_sources()
