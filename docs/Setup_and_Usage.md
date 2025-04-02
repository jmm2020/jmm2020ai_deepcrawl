# Crawl4AI Setup and Usage Guide

This document provides detailed instructions for setting up and using the Crawl4AI system, including the API bridge and web interface.

## System Components

The Crawl4AI system consists of several components:

1. **Core Components**:
   - `master_crawl.py` - Contains the `DeepCrawler` class for web crawling and content extraction
   - `db_adapter.py` - Manages connections to the Supabase database
   - `integrated_workflow.py` - Coordinates the overall crawling process

2. **API Bridge**:
   - `api_bridge.py` - FastAPI server that provides REST endpoints for the web interface

3. **Web Interface**:
   - Next.js application in the `workbench/web_frontend` directory

## Prerequisites

- Python 3.10+ with pip
- Node.js 18+ with npm
- Ollama installed and running locally
- Required Python packages (see `requirements.txt`)
- Required LLM models in Ollama:
  - At least one general LLM (e.g., llama2, gemma3:12b, gemma3:27b)
  - Embedding models:
    - `snowflake-arctic-embed2` (recommended for high quality)
    - `nomic-embed-text` (smaller, faster alternative)

## Setup Instructions

### 1. API Bridge Setup

1. Navigate to the `workbench/new_components` directory:
   ```
   cd workbench/new_components
   ```

2. Start the API bridge:
   ```
   python api_bridge.py
   ```
   
   The server will automatically try ports 1111-1120 if the default port 1111 is in use.

3. Verify the API bridge is running by checking:
   ```
   curl http://localhost:1111/
   ```
   
   You should see a response: `{"status":"healthy","message":"Crawl4AI API Bridge is running"}`

### 2. Web Interface Setup

1. Navigate to the `workbench/web_frontend` directory:
   ```
   cd workbench/web_frontend
   ```

2. Install dependencies (first time only):
   ```
   npm install
   ```

3. Start the Next.js development server:
   ```
   npm run dev
   ```
   
   The server will start on port 3112. If you encounter a port conflict (EADDRINUSE error), you can either:
   - Kill the existing process using that port:
     ```
     npx kill-port 3112
     ```
   - Or modify the package.json file to use a different port:
     ```
     "dev": "next dev -p 3113"
     ```

4. Access the web interface in your browser:
   ```
   http://localhost:3112/crawler
   ```

## Known Issues and Workarounds

### 1. Content Extraction Issues

**Issue**: Some page types (particularly CLI documentation) consistently fail content extraction.

**Impact**: Affects the completeness of crawled data, especially for technical documentation.

**Workaround**: 
- The system implements retry mechanisms with configurable attempts
- Content extraction has been enhanced with expanded selectors
- Rate limiting helps prevent overloading target servers

### 2. Supabase Connection Issues

**Issue**: Persistent issues with Supabase connection and queries.

**Impact**: Database storage may be unreliable, but local JSON file storage works correctly.

**Workaround**: 
- System automatically falls back to local JSON file storage
- Results are saved with timestamps for easy tracking
- Local files can be manually imported to database later

### 3. Large-Scale Crawl Performance

**Issue**: Mixed success with large crawls (~2600 pages), with systematic failures on certain page types.

**Impact**: May affect completeness of large-scale crawls.

**Workaround**:
- Break large crawls into smaller batches
- Use appropriate concurrent request settings
- Monitor and adjust rate limiting as needed

## Configuration Options

### Available Environment Variables

- `NEXT_PUBLIC_API_SERVER_URL` - URL for the API server (default: http://localhost:1111)
- `OLLAMA_HOST` - Custom host for Ollama (default: http://localhost:11434)
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase API key

### Command Line Options

API Bridge:
- Port selection happens automatically (1111-1120)

Web Interface:
- Port can be specified in package.json or with `--port` flag

## Usage Examples

### Basic Web Crawl

1. Access the web interface at `http://localhost:3112/crawler`
2. Configure crawl settings:
   - URL: Enter the starting URL (e.g., https://example.com)
   - Depth: Set crawl depth (recommended: 1-2)
   - Max Pages: Limit the number of pages (recommended: 5-50)
   - LLM Model: Select a model from dropdown
   - Embedding Model: Select `snowflake-arctic-embed2` (proven for 90+ pages)
3. Click "Start Crawling"
4. Monitor progress in the "Crawl Progress" section
5. View results in the "Results" tab

### Troubleshooting Steps

If you encounter issues:

1. Check both server logs (API bridge terminal and Next.js terminal)
2. Verify Ollama is running: `curl http://localhost:11434/api/tags`
3. Check port availability: `netstat -ano | findstr 3112` (Windows) or `lsof -i :3112` (Linux/Mac)
4. Ensure required models are installed in Ollama: `ollama list`

## Performance Considerations

### Hardware Requirements

- **CPU**: Multi-core processor recommended for parallel processing
- **Memory**: 8GB+ RAM recommended for large crawls
- **Storage**: SSD recommended for faster local file operations
- **Network**: Stable internet connection required

### Crawl Size Guidelines

Based on our latest testing with ~2600 pages:

1. **Small Crawls** (up to 100 pages):
   - Depth: 1-2
   - Concurrent Requests: 3-5
   - Expected Success Rate: 90%+

2. **Medium Crawls** (100-500 pages):
   - Depth: 1-2
   - Concurrent Requests: 5-10
   - Expected Success Rate: 80%+

3. **Large Crawls** (500+ pages):
   - Depth: 1
   - Concurrent Requests: 10-15
   - Expected Success Rate: 70%+
   - Consider breaking into smaller batches

### Optimization Tips

1. **Rate Limiting**:
   - Start with conservative settings
   - Monitor target server response times
   - Adjust based on server behavior

2. **Content Extraction**:
   - Use appropriate retry settings
   - Monitor failed pages for patterns
   - Consider specialized handlers for problematic page types

3. **Resource Management**:
   - Monitor system resource usage
   - Adjust concurrent requests based on CPU/memory
   - Use local file storage for reliability

## Real-Time Progress Monitoring

The system now provides enhanced progress monitoring:

1. **Terminal Output**:
   - Direct capture of all console output
   - Formatted with "[Terminal]" prefix
   - Real-time display in progress window

2. **WebSocket Communication**:
   - No ping mechanism required
   - Automatic connection closure
   - Clean resource management

3. **Error Reporting**:
   - Immediate display of errors
   - Clear success/failure indicators
   - Detailed progress information

## Next Steps

- Implement database connection reliability improvements
- Add model download functionality for missing models
- Enhance error handling and recovery
- Implement data visualization for crawled content 