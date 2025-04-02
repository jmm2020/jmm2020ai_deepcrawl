# Crawl4AI API Documentation

## Overview

The Crawl4AI API provides endpoints for managing web crawling operations, monitoring progress, and retrieving results. The API is built using FastAPI and provides real-time updates through WebSocket connections.

## Base URL

```
http://localhost:1111
```

## Endpoints

### 1. Start Crawl

```http
POST /api/crawl
```

Starts a new crawling operation with the specified parameters.

**Request Body:**
```json
{
    "url": "https://example.com",
    "depth": 2,
    "max_pages": 10,
    "llm_model": "gemma3:27b",
    "embedding_model": "snowflake-arctic-embed2:latest",
    "allowed_domains": ["example.com"],
    "system_prompt": "Summarize the key technical information on this page"
}
```

**Response:**
```json
{
    "job_id": "unique_job_id",
    "status": "accepted",
    "message": "Crawl job started successfully"
}
```

### 2. Get Job Status

```http
GET /api/status/{job_id}
```

Retrieves the current status and progress of a crawling operation.

**Response:**
```json
{
    "status": "running",
    "progress": {
        "pages_crawled": 5,
        "total_pages": 10,
        "current_url": "https://example.com/page5",
        "progress_logs": [
            "Starting crawl process...",
            "Processing page 1/10",
            "Generated embeddings for page 1"
        ]
    }
}
```

### 3. Get Available Models

```http
GET /api/ollama/models
```

Retrieves the list of available Ollama models.

**Response:**
```json
{
    "models": [
        {
            "name": "gemma3:27b",
            "size": 27000000000,
            "modified_at": "2025-03-31T20:00:00Z"
        },
        {
            "name": "snowflake-arctic-embed2:latest",
            "size": 5000000000,
            "modified_at": "2025-03-31T20:00:00Z"
        }
    ]
}
```

### 4. Get Crawl Results

```http
GET /api/results/{job_id}
```

Retrieves the complete results of a completed crawl operation.

**Response:**
```json
{
    "status": "completed",
    "results": {
        "pages": [
            {
                "url": "https://example.com",
                "title": "Example Page",
                "content": "Page content...",
                "embedding": [...],
                "metadata": {
                    "word_count": 500,
                    "chunks": 3
                }
            }
        ],
        "summary": {
            "total_pages": 10,
            "total_words": 5000,
            "average_chunks_per_page": 3
        }
    }
}
```

## WebSocket Updates

For real-time updates, the API supports WebSocket connections at:

```
ws://localhost:1111/ws/{job_id}
```

The WebSocket connection provides:
- Direct terminal output with "[Terminal]" prefix
- Real-time status updates
- Automatic connection closure on job completion

### Message Types

1. **Terminal Output**
```json
{
    "type": "terminal",
    "message": "[Terminal] Processing page: example.com",
    "status": "running"
}
```

2. **Status Updates**
```json
{
    "type": "status",
    "status": "complete",
    "message": "Job completed, closing connection"
}
```

### Connection Lifecycle

1. **Connection Establishment**
```json
{
    "type": "status",
    "status": "connected",
    "message": "WebSocket connection established"
}
```

2. **Job Progress**
- Terminal output is sent in real-time
- No ping mechanism required
- Messages are formatted with "[Terminal]" prefix

3. **Connection Closure**
- Automatic closure when job completes
- Clean disconnection with status message
- Resource cleanup on both ends

## Known Issues

1. **Content Extraction**
   - Some page types (particularly CLI documentation) fail to extract content
   - System implements retry mechanism but may need specialized handlers
   - Priority: High

2. **Database Integration**
   - Supabase connection and query issues persist
   - System falls back to local file storage
   - Priority: Medium

3. **Large-Scale Performance**
   - Mixed success with large crawls (~2600 pages)
   - Need to optimize concurrent request settings
   - Priority: Medium

## Recent Improvements

1. **WebSocket Communication**
   - Removed unnecessary ping mechanism
   - Added direct terminal output capture
   - Implemented proper connection closure
   - Added formatted output with "[Terminal]" prefix

2. **Error Handling**
   - Enhanced retry logic for content extraction
   - Better error reporting in terminal output
   - Improved connection error handling

3. **Performance**
   - Implemented rate limiting
   - Added concurrent request management
   - Optimized WebSocket communication

## Error Responses

All endpoints may return the following error responses:

```json
{
    "error": "Error message",
    "status": "error",
    "details": {
        "code": "ERROR_CODE",
        "message": "Detailed error message"
    }
}
```

Common error codes:
- `INVALID_PARAMETERS`: Request parameters are invalid
- `MODEL_NOT_FOUND`: Specified Ollama model is not available
- `JOB_NOT_FOUND`: Requested job ID does not exist
- `DATABASE_ERROR`: Database operation failed
- `CRAWL_ERROR`: Crawler encountered an error during execution

## Rate Limiting

The API implements basic rate limiting:
- 100 requests per minute per IP address
- 1000 requests per hour per IP address

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1617235200
``` 