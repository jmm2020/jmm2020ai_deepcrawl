# Crawl4AI

A comprehensive web crawling, content extraction, and knowledge base creation system with LLM integration.

## Overview

Crawl4AI is a Python-based web crawler specifically designed for AI applications. It extracts content from websites, processes it with LLMs, generates embeddings, and stores everything in a vector database for easy retrieval and AI-assisted search.

### Key Features

- **Deep Crawling**: Configurable depth and breadth for website exploration
- **Specialized Content Extraction**: Intelligent selectors for different documentation types
- **LLM Integration**: Automatic content summarization and categorization
- **Vector Embeddings**: Generate embeddings for semantic search
- **Supabase Integration**: Store crawled data in a vector database
- **Modern Web UI**: Configure crawls and view results
- **CLI Documentation Support**: Specialized handling for command-line documentation

## Project Structure

- **api/**: API server implementation with FastAPI
- **core/**: Core crawler components
- **utils/**: Utility functions and specialized content extractors
- **scripts/**: Management scripts
- **tests/**: Unit tests
- **docs/**: Project documentation
- **frontend/**: Web UI components

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- [Ollama](https://ollama.ai/) for local LLM usage
- [Supabase](https://supabase.com/) account or local instance

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/crawl4ai.git
   cd crawl4ai
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

4. Download required LLM models via Ollama:
   ```bash
   ollama pull gemma3:27b
   ollama pull snowflake-arctic-embed2:latest
   ```

### Running the Application

The easiest way to run the application is with the included script:

```bash
cd scripts
./start-all.bat  # For Windows
```

For individual components:

1. **API Server**:
   ```bash
   cd api
   python api_bridge.py
   ```

2. **Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

The web interface will be available at http://localhost:3112/crawler.

## Usage

### Basic Crawling

1. Open the web interface
2. Enter a starting URL
3. Configure crawl depth and other parameters
4. Click "Start Crawl"
5. Monitor progress in real-time
6. View and explore results when crawling completes

### Multi-URL Crawling

For comprehensive website coverage:

```bash
curl -X POST http://localhost:1111/api/crawl-many \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com", "https://example.com/docs"],
    "depth": 2,
    "max_pages": 100,
    "model": "gemma3:27b",
    "max_concurrent_requests": 5
  }'
```

### Sitemap Integration

```python
from core.master_crawl import DeepCrawler

# Parse sitemap to extract URLs
urls = DeepCrawler.parse_sitemap("https://example.com/sitemap.xml")

# Create crawler and process the URLs
crawler = DeepCrawler()
crawler.crawl_many(urls, max_depth=1, max_concurrent_requests=5)
```

## Development

See [PROGRESS.md](docs/PROGRESS.md) for current development status and [NEXT_STEPS.md](docs/NEXT_STEPS.md) for planned features.

For GitHub repository setup and workflow guidelines, see [GITHUB_SETUP.md](docs/GITHUB_SETUP.md).

## Testing

Run the test suite:

```bash
python -m unittest discover tests
```

## License

[MIT License](LICENSE) 