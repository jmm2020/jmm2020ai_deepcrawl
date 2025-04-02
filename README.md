# Crawl4AI Web Crawler - Reorganized Structure

This is a clean, reorganized version of the Crawl4AI project with only essential files needed for operation.

## Directory Structure

- **api/**: API server implementation
  - `api_bridge.py`: Main API server
  - `config.py`: Configuration settings
  - `start_api.bat`: API startup script

- **core/**: Core crawler components
  - `master_crawl.py`: Main crawler implementation
  - `db_adapter.py`: Database integration
  - `integrated_workflow.py`: Workflow orchestration

- **utils/**: Utility functions
  - `paths.py`: Path handling utilities
  - `__init__.py`: Module initialization

- **scripts/**: Management scripts
  - `start-all.bat`: Main startup script
  - `stop-all.bat`: Shutdown script

- **docs/**: Documentation
  - `API.md`: API reference
  - `Setup_and_Usage.md`: Setup instructions
  - `PROGRESS.md`: Development status

- **frontend/**: Web UI components (TBD)

- **results/**: Directory for storing crawl results

## Startup Instructions

1. Use `scripts/start-all.bat` to start both the API server and frontend

## Development Notes

This structure separates concerns and removes redundant files from the original project. Path references and imports have been updated to reflect the new organization.

## Version 0.0.6

This project provides a robust web crawling solution with Supabase database integration.

## Quick Start

The easiest way to run the application is to use the included startup script:

```
cd workbench
start-all.bat
```

This will start both the API server and the frontend application, and you can access the web interface at http://localhost:3112/crawler.

## Main Features

- **Web Crawling**: Crawl websites with depth and page limit controls
- **Content Extraction**: Extract structured content from web pages
- **Embedding Generation**: Generate embeddings for the extracted content
- **Multi-Domain Support**: Crawl across allowed domains
- **Multi-URL Crawling**: Crawl multiple URLs in parallel with optimal resource utilization
- **Sitemap Integration**: Extract URLs from sitemap.xml files for comprehensive crawling
- **Parallelization**: Configure concurrent requests for optimal performance
- **Local Storage**: Save results to local JSON files
- **Supabase Integration**: Option to store results in a Supabase database
- **Interactive UI**: Modern web interface for configuring crawls and viewing results

## Core Components

- **API Server**: FastAPI-based server providing endpoints for crawling and retrieving results
- **Frontend**: Next.js application with a modern UI for interacting with the API
- **Crawler Engine**: Python-based crawler for extracting and processing web content
- **Database Adapter**: Interface for storing and retrieving data from Supabase

## API Endpoints

The API server runs on port 1111 by default and provides the following endpoints:

- **POST /api/crawl**: Start a new crawl job with a single URL
- **POST /api/crawl-many**: Start a multi-URL crawl job with parallelization
- **GET /api/status/{job_id}**: Check the status of a crawl job
- **GET /api/results/{job_id}**: Get the complete results of a crawl job
- **GET /api/results-files**: List all available crawl result files
- **GET /api/models**: Get a list of available LLM models
- **GET /api/database-status**: Check the status of the Supabase connection

## Frontend

The frontend runs on port 3112 by default and provides a modern web interface for:

- Configuring and starting crawl jobs
- Monitoring crawl progress in real-time
- Viewing crawl results with structured content
- Chatting with the crawled knowledge base (coming soon)

## Required Models

The crawler requires the following Ollama models:

1. **LLM Model**: `gemma3:27b` (recommended) or `llama3:8b` (for lower resource systems)
2. **Embedding Model**: `snowflake-arctic-embed2:latest` (required - make sure to use the exact name including `:latest`)

To download these models:
```
ollama pull gemma3:27b
ollama pull snowflake-arctic-embed2:latest
```

## Multi-URL Crawling

Website structure often limits the crawler's ability to discover all pages through a single starting URL. To address this, we've implemented multi-URL crawling capabilities:

1. **Multiple Entry Points**: Crawl from multiple starting URLs simultaneously
2. **Sitemap Integration**: Automatically extract URLs from website sitemaps
3. **Parallelization Controls**: Adjust concurrent requests for optimal performance

### Using Multi-URL Crawling

You can use multi-URL crawling in several ways:

#### Via Python API

```python
from integrated_workflow import run_multi_url_crawl

# Configure crawl parameters
params = {
    "urls": ["https://example.com", "https://example.com/docs", "https://example.com/blog"],
    "depth": 2,
    "max_pages": 100,
    "llm_model": "gemma3:27b",
    "embedding_model": "snowflake-arctic-embed2:latest",
    "allowed_domains": ["example.com"],
    "max_concurrent_requests": 5
}

# Run the multi-URL crawl
result = run_multi_url_crawl(params)

# Process results
print(f"Crawled {result['pages_crawled']} pages across {result['starting_urls']} starting points")
```

#### Via REST API

```bash
curl -X POST http://localhost:1111/api/crawl-many \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com", "https://example.com/docs", "https://example.com/blog"],
    "depth": 2,
    "max_pages": 100,
    "model": "gemma3:27b",
    "max_concurrent_requests": 5
  }'
```

#### Via Sitemap

```python
from master_crawl import DeepCrawler

# Parse sitemap to extract URLs
urls = DeepCrawler.parse_sitemap("https://example.com/sitemap.xml")

# Create crawler and process the URLs
crawler = DeepCrawler(
    llm_model="gemma3:27b",
    embedding_model="snowflake-arctic-embed2:latest"
)
crawler.crawl_many(urls, max_depth=1, max_concurrent_requests=5)
```

## Parallelization Options

The crawler uses a ThreadPoolExecutor-based concurrency mechanism to control parallel requests. You can adjust these settings to optimize performance:

- **max_concurrent_requests**: Controls the number of simultaneous page requests

We recommend the following settings based on our testing:

- Small websites: 3-5 concurrent requests
- Medium websites: 5-10 concurrent requests
- Large websites: 10-15 concurrent requests

These settings are exposed via the Python API and REST API parameters.

## Known Issues and Limitations

### Database Integration
- **Database Connection**: Currently experiencing issues with Supabase connection and queries.
- The system successfully crawls pages but may have trouble storing data in Supabase.
- All crawled data is saved to local JSON files as a fallback.
- Recent crawl of ~2600 pages showed mixed success, with systematic failures on certain page types.
- A post-processing script is now available to retry inserting JSON files into Supabase (see below).

### Content Extraction
- **Page Structure Variations**: Some pages (particularly CLI documentation) may fail content extraction.
- The system has been updated with improved retry mechanisms and expanded content selectors.
- Rate limiting and concurrent request management have been implemented to prevent overloading.

### WebSocket Improvements
- **Real-time Updates**: The WebSocket connection has been enhanced to:
  - Remove unnecessary ping mechanism
  - Capture and display all terminal output directly
  - Properly close connections when jobs complete
  - Format terminal output with "[Terminal]" prefix

### Server Management
- **Process Termination**: Server management scripts handle process cleanup more reliably.
- Both API and frontend servers can be restarted cleanly using the provided scripts.
- WebSocket connections are properly closed to prevent resource leaks.

### Work in Progress Features
- **Multi-URL Crawling**: While functional, may need optimization for large-scale crawls.
- **Content Processing**: Some page types may require specialized handling for better extraction.
- **Database Integration**: Working on improving reliability of Supabase connections and data storage.

### Development Status
This project is actively under development. Recent improvements include:
- Enhanced error handling and retries for content extraction
- Improved WebSocket communication
- Better rate limiting and concurrent request management
- More robust server process management

## Development Tasks

See [PROGRESS.md](docs/PROGRESS.md) for current development status and upcoming tasks.

## Running Individual Components

If you need to run components individually:

1. **API Server**:
   ```
   cd workbench/new_components
   python api_bridge.py
   ```

2. **Frontend**:
   ```
   cd workbench/web_frontend
   npm run dev
   ```

## Testing Multi-URL Crawling

To test the multi-URL crawling feature:

```
cd workbench
python test_multi_url_crawl.py
```

For testing with sitemap parsing:

```
cd workbench
python test_multi_url_crawl.py --use-sitemap
```

## Environment Configuration

The frontend uses environment variables in `.env.local`:

- `NEXT_PUBLIC_API_SERVER_URL`: URL of the API server (default: http://localhost:1111)
- `NEXT_PUBLIC_PORT`: Port for the frontend server (default: 3112)

## Documentation

For more detailed information, see the documentation in the `docs/` directory:

- [Documentation Index](docs/INDEX.md): Central hub for all documentation
- [Setup and Usage](docs/Setup_and_Usage.md): Getting started with the system
- [API Reference](docs/API.md): Complete API reference and endpoints
- [Progress Tracking](docs/PROGRESS.md): Current development status and next steps
- [Next Steps](docs/NEXT_STEPS.md): Planned tasks and action items for future development
- [Troubleshooting](docs/TROUBLESHOOTING.md): Solutions for common issues
- [Testing Guide](docs/TESTING.md): Comprehensive testing procedures
- [JSON Processing](docs/JSON_PROCESSING.md): Guide for the JSON post-processing tools

### Development Documentation

For contributors and developers:

- [Contributing Guidelines](docs/CONTRIBUTING.md): How to contribute to the project
- [Code Standards](docs/CODE_STANDARDS.md): Coding standards and best practices
- [Migration Summary](docs/MIGRATION_SUMMARY.md): Project migration details
- [Terminal Output Fixes](docs/TERMINAL_OUTPUT_FIXES.md): WebSocket and terminal output improvements
- [Master Rule](docs/MASTER_RULE.md): **IMPORTANT** - Critical guidelines for maintaining system integrity
- [Version History](docs/VERSION_HISTORY.md): Release history and version changes

## Main Files

- master_crawl.py: Main crawler implementation
- db_adapter.py: Supabase integration
- integrated_workflow.py: Complete workflow script
- gui_test.py: Graphical interface for testing
- run_gui.bat: Batch script to easily launch the GUI
- test_multi_url_crawl.py: Test script for multi-URL crawling functionality
- logs/: Directory containing test logs and results

## Documentation

- [API Documentation](docs/API.md): Complete API reference and endpoints
- [Web GUI Integration](docs/Web_GUI_Integration.md): How the web GUI interfaces with core components
- [Data Flow Diagram](docs/Data_Flow_Diagram.md): Detailed data flow between all components
- [Web GUI Requirements](docs/Web_GUI_Requirements.md): Technical requirements for web GUI implementations
- [Core Testing](docs/CORE_TESTING.md): Core testing procedures and results
- [Master Rule](docs/MASTER_RULE.md): **IMPORTANT** - Critical guidelines for maintaining system integrity
- [Progress Tracking](docs/PROGRESS.md): Current development status and next steps

## Core Development Guidelines

**MASTER RULE: DO NOT MODIFY THE CORE FILES DIRECTLY**

The core files (master_crawl.py, db_adapter.py, and integrated_workflow.py) form the stable foundation of the system and should not be directly modified. Instead, use the wrapper, integration, or extension patterns described in the [Master Rule](docs/MASTER_RULE.md) document.

This rule ensures system stability, interface consistency, and backward compatibility for all dependent applications.

## Integration

To integrate the crawler into your own application:

```python
from integrated_workflow import run_crawl_from_params

# Configure crawl parameters
params = {
    "url": "https://example.com",
    "depth": 2,
    "max_pages": 10,
    "llm_model": "gemma3:27b",
    "embedding_model": "snowflake-arctic-embed2:latest",
    "allowed_domains": ["example.com"],
    "system_prompt": "Summarize the key technical information on this page",
    "output": "crawl_results.json",
    "skip_db": False,
    "max_concurrent_requests": 5  # Control parallelization
}

# Run the crawl
result = run_crawl_from_params(params)

# Process results
print(f"Crawled {result['pages_crawled']} pages")
print(f"Output saved to {result['output_file']}")
```

For multi-URL crawling:

```python
from integrated_workflow import run_multi_url_crawl

# Configure crawl parameters
params = {
    "urls": ["https://example.com", "https://example.com/docs", "https://example.com/blog"],
    "depth": 2,
    "max_pages": 100,
    "llm_model": "gemma3:27b",
    "embedding_model": "snowflake-arctic-embed2:latest",
    "allowed_domains": ["example.com"],
    "output": "multi_crawl_results.json",
    "max_concurrent_requests": 10  # Higher concurrency for multi-URL crawling
}

# Run the multi-URL crawl
result = run_multi_url_crawl(params)

# Process results
print(f"Crawled {result['pages_crawled']} pages across {len(result['starting_urls'])} starting points")
```

You can also use the sitemap integration for more comprehensive crawling:

```python
from master_crawl import DeepCrawler
from integrated_workflow import run_multi_url_crawl

# Parse sitemap to get URLs
urls = DeepCrawler.parse_sitemap("https://example.com/sitemap.xml")

# Configure crawl parameters with the extracted URLs
params = {
    "urls": urls,
    "depth": 1,  # Shallow depth since we're using sitemap URLs
    "max_pages": 200,
    "llm_model": "gemma3:27b",
    "embedding_model": "snowflake-arctic-embed2:latest",
    "max_concurrent_requests": 10
}

# Run the crawl
result = run_multi_url_crawl(params)
```

See [API Documentation](docs/API.md) for more details on integration.

## Features

- **Model Preloading**: Use the "Preload Model" button to load Ollama models before crawling
- **Heartbeat Mechanism**: Automatically checks if Ollama models are loaded and ready
- **Custom System Prompts**: Customize how the LLM summarizes content
- **Multi-URL Crawling**: Process multiple URLs in parallel for better site coverage
- **Sitemap Integration**: Parse sitemap.xml files to extract all available URLs
- **Parallelization Controls**: Fine-tune concurrent request settings for optimal performance
- **Rich Embeddings**: Generate and store embeddings for all crawled content
- **Content Chunking**: Automatically split long content into manageable chunks for better processing
- **Real-time Progress Updates**: Monitor crawl progress via WebSocket connection

## Server Management Scripts

### Starting the Servers

The `start-all.bat` script is designed to properly start both the API server and the web frontend. It includes functionality to automatically stop any existing servers running on the required ports before starting new ones.

```
cd workbench
.\start-all.bat
```

This script will:
1. Check for and terminate any processes using ports 1111 (API server) and 3112 (web frontend)
2. Wait briefly for processes to terminate
3. Start the API server in a new terminal window
4. Start the web frontend in a new terminal window

### Stopping the Servers

To stop all running servers, use the `stop-all.bat` script:

```
cd workbench
.\stop-all.bat
```

This script will:
1. Find and terminate any processes using ports 1111 and 3112
2. Find and terminate any Python processes that might be running the API server
3. Find and terminate any Node.js processes that might be running the web frontend

### Post-Processing JSON Files

If the crawler successfully generates JSON files but fails to insert the data into Supabase, you can use the `import_json_to_supabase.bat` script to retry the database insertion.

First, list available crawl result files:

```
cd workbench/scripts
import_json_to_supabase.bat list
```

This will display all available crawl result JSON files with their timestamps and sizes. Then, import the desired file:

```
import_json_to_supabase.bat results\crawl_results_20250402_123456.json
```

This script:
1. Checks for existing records in Supabase to avoid duplicates
2. Processes the JSON file in batches to prevent overwhelming the database
3. Implements retry logic for failed insertions
4. Provides detailed logs of successes, failures, and skipped duplicates
5. Maintains data integrity by avoiding duplicate insertions

#### Advanced Usage:

```
import_json_to_supabase.bat path\to\file.json [batch_size] [retry_count] [delay]
```

Parameters:
- `batch_size`: Number of records to process in each batch (default: 10)
- `retry_count`: Number of retries for failed insertions (default: 3)
- `delay`: Delay in seconds between batches (default: 1.0)

For example, to process 20 records at a time with 5 retry attempts and a 2-second delay:
```
import_json_to_supabase.bat results\crawl_results_20250402_123456.json 20 5 2
```

A detailed log file is generated in the `logs` directory for each import session.

#### Testing Post-Processing Capabilities

To verify the post-processing functionality works correctly, follow these testing steps:

1. **Initial Setup Test**:
   ```
   cd workbench/scripts
   import_json_to_supabase.bat list
   ```
   Verify you can see the list of available JSON files.

2. **Small-Scale Import Test**:
   ```
   import_json_to_supabase.bat results\[small_file].json 5 3 1.0
   ```
   Choose a small file (under 50 pages) for initial testing with a small batch size.

3. **Duplicate Detection Test**:
   Run the same import command again to verify duplicate detection works:
   ```
   import_json_to_supabase.bat results\[same_file].json
   ```
   Check the logs to confirm duplicates were identified and skipped.

4. **Large File Test**:
   For larger files, increase batch size but also increase delay:
   ```
   import_json_to_supabase.bat results\[large_file].json 20 5 2.0
   ```
   
5. **Validation**:
   After importing, check the Supabase database to verify the data was inserted correctly.
   - Count records to ensure they match successful imports
   - Verify content and embeddings are intact
   - Test search functionality with the imported records

Each import process generates a detailed log file in the `logs` directory with the format `supabase_import_YYYYMMDD_HHMMSS.log`. Review these logs to analyze import performance and identify any issues.

**Important**: Always use these scripts to manage the servers to avoid port conflicts and ensure proper operation of the WebSocket connections and progress display.
