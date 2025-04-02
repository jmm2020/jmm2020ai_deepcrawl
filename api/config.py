"""
Configuration for the Crawl4AI API Bridge
"""

# API Settings
API_HOST = "0.0.0.0"
API_PORT = 1111

# Crawler Settings
DEFAULT_MAX_DEPTH = 2
DEFAULT_MAX_PAGES = 50
DEFAULT_MODEL = "llama2"
DEFAULT_SYSTEM_PROMPT = "Extract key information from the webpage including the title, main content, key topics, and important links."

# Storage Settings
RESULTS_DIR = "crawl_results"

# Job Settings
JOB_TIMEOUT = 3600  # 1 hour
CLEANUP_INTERVAL = 3600  # Clean up completed jobs after 1 hour 