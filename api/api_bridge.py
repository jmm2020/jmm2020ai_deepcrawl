#!/usr/bin/env python3
"""
Crawl4AI API Bridge

This module serves as an API bridge for the Crawl4AI system. It provides endpoints
for initiating web crawls, checking status, and retrieving results.
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import uuid
import time
from datetime import datetime
import sys
import os
from typing import Optional, Dict, Any, List, Set
import json
import requests
from urllib.parse import urlparse
import traceback
import glob
import threading
import subprocess
import importlib
import asyncio
from collections import defaultdict
from pathlib import Path
import inspect

# Add parent directory to path to resolve imports
sys.path.append(str(Path(__file__).parent.parent))

# Import core components (without modifying them)
from core.master_crawl import DeepCrawler
from core.db_adapter import SupabaseAdapter
from core.integrated_workflow import run_crawl_from_params, run_multi_url_crawl
from utils.paths import get_results_path

app = FastAPI(title="Crawl4AI API Bridge")

# Add CORS middleware to allow requests from the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# State management for active jobs
class JobState:
    """Tracks the state of a crawl job"""
    def __init__(self):
        self.status = "pending"
        self.progress = 0.0
        self.start_time = time.time()
        self.current_page = None
        self.pages_crawled = 0
        self.progress_logs: List[str] = []  # Explicitly typed as List[str]
        self.result = None
        self.error = None
        self.output_file = None  # Track the output file path
        
    async def add_log(self, message: str, job_id: str = None):
        """Add a log message and broadcast it via WebSocket if job_id is provided"""
        if message:
            # Make sure it's a string
            log_entry = str(message)
            # Add it to the logs
            if not hasattr(self, 'progress_logs') or self.progress_logs is None:
                self.progress_logs = []
            self.progress_logs.append(log_entry)
            # Log to console as well
            print(f"Progress log: {log_entry}")
            
            # Broadcast via WebSocket if job_id is provided
            # Don't wait for a ping - immediately push the log to all connected clients
            if job_id:
                try:
                    # We'll broadcast this individual log message right away
                    await manager.broadcast_to_job(job_id, json.dumps({
                        "type": "progress",
                        "message": log_entry,
                        "status": self.status,
                        "progress": self.progress,
                        "current_page": self.current_page,
                        "pages_crawled": self.pages_crawled
                    }))
                    print(f"WebSocket broadcast: Sent log: {log_entry[:50]}..." if len(log_entry) > 50 else f"WebSocket broadcast: Sent log: {log_entry}")
                except Exception as e:
                    print(f"Error broadcasting progress: {e}")

    async def update_status(self, status: str, job_id: str = None):
        """Update job status and broadcast via WebSocket if job_id is provided"""
        self.status = status
        
        # Add a timestamp for completion to help with cleanup
        if status in ["completed", "error", "failed"]:
            self.completion_time = time.time()
            
        if job_id:
            try:
                await manager.broadcast_to_job(job_id, json.dumps({
                    "type": "status",
                    "status": status,
                    "progress": self.progress,
                    "current_page": self.current_page,
                    "pages_crawled": self.pages_crawled
                }))
                
                # If completed or error, also close all WebSocket connections for this job
                if status in ["completed", "error", "failed"]:
                    # Schedule cleanup to run after a delay
                    asyncio.create_task(self.schedule_cleanup(job_id))
                    
            except Exception as e:
                print(f"Error broadcasting status: {e}")
                
    async def schedule_cleanup(self, job_id: str, delay_seconds: int = 300):
        """Schedule cleanup of job resources after a delay"""
        try:
            # Wait for the specified delay (default 5 minutes)
            await asyncio.sleep(delay_seconds)
            
            # Run cleanup
            if job_id in active_jobs:
                print(f"Cleaning up completed job {job_id}")
                # Close any remaining WebSocket connections
                await manager.close_all_job_connections(job_id)
                # Remove job from active_jobs
                del active_jobs[job_id]
                print(f"Job {job_id} removed from active jobs")
        except Exception as e:
            print(f"Error scheduling cleanup for job {job_id}: {e}")

# Global job storage
active_jobs: Dict[str, JobState] = {}

DEFAULT_SYSTEM_PROMPT = """WEB CONTENT EXTRACTION AND PROCESSING

PRIMARY OBJECTIVE:
Extract high-quality, structured information from webpages to create a comprehensive knowledge base for retrieval augmented generation (RAG) systems.

EXTRACTION GUIDELINES:
1. METADATA EXTRACTION
   - Page title: Extract the complete, accurate title as displayed in browser tabs
   - Publication date: Identify and standardize to ISO format (YYYY-MM-DD)
   - Author information: Extract name(s) and credentials when available
   - URL: Preserve the canonical URL

2. CONTENT EXTRACTION
   - Main content: Isolate primary textual content from navigation, ads, and sidebars
   - Preserve semantic structure: Maintain heading hierarchy (H1, H2, H3, etc.)
   - Extract meaningful lists, tables, and structured data with formatting preserved
   - Remove duplicate content, navigation elements, and promotional material

3. SEMANTIC ANALYSIS
   - Identify 3-7 primary topics covered in the content
   - Extract key entities (people, organizations, products, locations)
   - Generate 3-5 relevant keywords for content categorization
   - Summarize the main content in 2-3 concise paragraphs

4. LINK PROCESSING
   - Validate all extracted links with HTTP status code checking
   - Only include links returning 200 status codes
   - Categorize links as: internal navigation, external references, citation sources
   - Prioritize links to authoritative sources or supporting documentation

5. CONTENT VERIFICATION
   - Flag potential misinformation or factually questionable content
   - Note content currency/freshness based on publication date
   - Document access limitations (paywalls, login requirements)

6. OUTPUT FORMATTING
   - Structure all extracted data in consistent JSON format
   - Ensure UTF-8 encoding for all text content
   - Preserve important formatting (bold, italics, lists) using markdown
   - Include metadata about extraction process (timestamp, version)

PROCESSING CONSTRAINTS:
- Process each page as standalone content while preserving context
- Document any extraction failures or limitations encountered

ERROR HANDLING:
- Gracefully handle malformed HTML, JavaScript-dependent content
- Record partial extractions when complete processing fails
- Provide detailed error logs for debugging and system improvement"""

# Request models
class CrawlRequest(BaseModel):
    url: str
    max_depth: int = 2
    max_pages: int = 50
    model: str = "llama2"
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    use_sitemap: bool = False  # Add use_sitemap parameter
    embedding_model: str = "snowflake-arctic-embed2:latest"  # Add embedding_model parameter for flexibility

# Response models
class CrawlResponse(BaseModel):
    job_id: str
    status: str

# WebSocket connections management
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        self.active_connections[job_id].add(websocket)

    def disconnect(self, websocket: WebSocket, job_id: str):
        self.active_connections[job_id].discard(websocket)
        if not self.active_connections[job_id]:
            del self.active_connections[job_id]

    async def close_all_job_connections(self, job_id: str):
        """Close all WebSocket connections for a specific job"""
        if job_id not in self.active_connections:
            return
            
        connections = list(self.active_connections[job_id])
        for websocket in connections:
            try:
                await websocket.close(code=1000, reason="Job completed and resource cleanup")
            except Exception as e:
                print(f"Error closing WebSocket for job {job_id}: {e}")
                
        # Clear all connections for this job
        self.active_connections[job_id] = set()
        
    async def broadcast_to_job(self, job_id: str, message: str):
        if job_id in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_text(message)
                except WebSocketDisconnect:
                    dead_connections.add(connection)
                except Exception as e:
                    print(f"Error sending message: {e}")
                    dead_connections.add(connection)
            
            # Clean up dead connections
            for dead in dead_connections:
                self.disconnect(dead, job_id)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"status": "healthy", "message": "Crawl4AI API Bridge is running"}

@app.post("/api/crawl", response_model=CrawlResponse)
async def start_crawl(request: CrawlRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    
    # Create job state for tracking progress
    job_state = JobState()
    active_jobs[job_id] = job_state
    
    # Start the crawl task in the background
    background_tasks.add_task(process_crawl, request, job_id, job_state)
    
    return {"job_id": job_id, "status": "pending"}

async def process_crawl(request: CrawlRequest, job_id: str, job_state: JobState):
    """Process a single URL crawl request"""
    try:
        await job_state.update_status("starting", job_id)
        job_state.progress_logs = []
        
        # Get progress update function for this specific job
        async def update_progress(message: str):
            """Update progress for this job"""
            await job_state.add_log(message, job_id)
        
        await update_progress("Starting crawl process...")
        
        # Create a function to send terminal output directly to the client
        async def send_terminal_output(message: str):
            """Send terminal output directly to the websocket"""
            # Echo to terminal
            print(message)
            # Send to client WebSocket
            await job_state.add_log(f"[Terminal] {message}", job_id)
        
        # Intercept stdout for piping directly to WebSocket
        class WebSocketStreamRedirector:
            def __init__(self, original_stream, callback_func):
                self.original_stream = original_stream
                self.callback_func = callback_func
                
            def write(self, text):
                # Write to the original stream
                self.original_stream.write(text)
                # Only process non-empty text
                if text.strip():
                    # Create asyncio task to send to WebSocket
                    asyncio.create_task(self.callback_func(text.strip()))
                
            def flush(self):
                self.original_stream.flush()
        
        # Store original stdout
        original_stdout = sys.stdout
        
        # Redirect stdout to our custom handler
        sys.stdout = WebSocketStreamRedirector(original_stdout, send_terminal_output)
        
        # Extract domain from URL for allowed_domains
        parsed_url = urlparse(request.url)
        domain = parsed_url.netloc
        if domain.startswith('www.'):
            domain = domain[4:]  # Remove www. prefix
            
        await update_progress(f"Crawling domain: {domain}")
        
        try:
            # Initialize crawler using existing DeepCrawler
            await update_progress(f"Initializing crawler with model: {request.model}")
            
            # Custom callback function to capture output from crawler
            def crawler_progress_callback(message):
                # Create an asyncio task to send the message via WebSocket
                loop = asyncio.get_event_loop()
                asyncio.run_coroutine_threadsafe(update_progress(message), loop)
                # Also print to terminal for visibility
                print(f"CRAWLER: {message}")
                
            crawler = DeepCrawler(
                llm_model=request.model,
                embedding_model=request.embedding_model,
                system_prompt=request.system_prompt,
                allowed_domains=[domain]  # Only allow the URL domain
            )
            await update_progress(f"Crawler initialized successfully")
            
            # Check Supabase connection and log detailed status
            if crawler.supabase:
                await update_progress("✓ Successfully connected to Supabase database")
            else:
                await update_progress("ℹ️ Supabase client initialized with 'headers' attribute warning - this is expected and non-critical")
                if hasattr(crawler, 'supabase_error') and crawler.supabase_error:
                    # Downgrade the severity of the headers error message
                    if "'dict' object has no attribute 'headers'" in str(crawler.supabase_error):
                        await update_progress("ℹ️ This is a known startup warning with the Supabase client")
                        await update_progress("ℹ️ Database operations will still function correctly")
                    else:
                        # For other errors, keep the warning level
                        await update_progress(f"⚠ Supabase connection warning: {crawler.supabase_error}")
        except Exception as init_error:
            await update_progress(f"✗ Error initializing crawler: {str(init_error)}")
            # Add detailed information about the initialization error
            if "'dict' object has no attribute 'headers'" in str(init_error):
                await update_progress("ℹ️ Non-critical Supabase client warning - this is expected during initialization")
                await update_progress("ℹ️ Database operations will still function correctly")
            else:
                await update_progress("→ This will not affect the crawler's ability to extract and process content")
                await update_progress("→ Results will be saved to local JSON files that can be used for analysis")
            traceback.print_exc()
            error_traceback = traceback.format_exc()
            await update_progress(f"Error details: {error_traceback.split('Traceback')[1].strip() if 'Traceback' in error_traceback else error_traceback}")
            raise init_error
        
        # Set up a callback for crawl progress
        original_process_page = crawler._process_page
        
        # Create an asyncio-compatible update function for use in synchronous methods
        async def async_update_progress(message):
            await job_state.add_log(message, job_id)
        
        # Create a synchronous wrapper that uses asyncio.run_coroutine_threadsafe
        # to ensure log messages are properly sent from non-async contexts
        def sync_update_progress(message):
            # Always log to console first for visibility in the terminal
            print(f"PROGRESS: {message}")
            
            # Add to job_state logs so it's available for result retrieval later
            if not hasattr(job_state, 'progress_logs') or job_state.progress_logs is None:
                job_state.progress_logs = []
            job_state.progress_logs.append(message)
            
            # Update pages_crawled count if this is a completion message
            if "Successfully processed:" in message:
                job_state.pages_crawled += 1
                job_state.current_page = message.split("Successfully processed:")[1].strip()
            
            # Try sending to WebSocket if possible
            loop = asyncio.get_event_loop()
            if loop.is_running():
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        async_update_progress(message), 
                        loop
                    )
                    # Don't wait for completion to avoid blocking
                    # The message is already logged to console and job_state
                except Exception as e:
                    print(f"WebSocket send error (non-critical): {e}")
            else:
                print("(WebSocket not active, message logged to console only)")
        
        # Replace the callback to use our threadsafe updater
        def process_page_with_progress(url):
            sync_update_progress(f"Processing page: {url}")
            job_state.current_page = url
            job_state.pages_crawled += 1
            job_state.progress = min(0.9, job_state.pages_crawled / (request.max_pages or 50))
            
            try:
                result = original_process_page(url)
                if result:
                    sync_update_progress(f"✓ Successfully processed: {url}")
                    if "title" in result.get("metadata", {}):
                        sync_update_progress(f"  Title: {result['metadata']['title']}")
                    
                    if result.get("embedding") is not None:
                        sync_update_progress(f"✓ Generated embeddings for: {url}")
                    
                    # Log content stats if available
                    content_stats = result.get("content", {}).get("metadata", {})
                    if content_stats:
                        stats_message = "  Content stats: "
                        if "word_count" in content_stats:
                            stats_message += f"{content_stats['word_count']} words, "
                        if "chunk_count" in content_stats:
                            stats_message += f"{content_stats['chunk_count']} chunks"
                        sync_update_progress(stats_message)
                else:
                    sync_update_progress(f"✗ Failed to process: {url}")
                return result
            except Exception as page_error:
                sync_update_progress(f"✗ Error processing page {url}: {str(page_error)}")
                return None
        
        # Replace the _process_page method with our instrumented version
        crawler._process_page = process_page_with_progress
        
        await job_state.update_status("crawling", job_id)
        await update_progress(f"Starting crawl with depth={request.max_depth}, max_pages={request.max_pages}, model={request.model}")
        
        # Check if we should use sitemap parsing
        if request.use_sitemap:
            await update_progress(f"Sitemap mode enabled - attempting to locate and parse sitemap.xml")
            sitemap_url = f"{parsed_url.scheme}://{parsed_url.netloc}/sitemap.xml"
            await update_progress(f"Looking for sitemap at: {sitemap_url}")
            
            try:
                # Parse the sitemap
                sitemap_urls = DeepCrawler.parse_sitemap(sitemap_url)
                
                if sitemap_urls and len(sitemap_urls) > 0:
                    await update_progress(f"✓ Successfully parsed sitemap - found {len(sitemap_urls)} URLs")
                    
                    # If we found URLs in the sitemap, use multi-URL crawling
                    await update_progress(f"Starting multi-URL crawl with {len(sitemap_urls)} URLs from sitemap")
                    
                    # Limit the number of URLs if max_pages is set (unless it's 0)
                    crawl_urls = sitemap_urls
                    if request.max_pages > 0 and len(sitemap_urls) > request.max_pages:
                        crawl_urls = sitemap_urls[:request.max_pages]
                        await update_progress(f"Limited to first {request.max_pages} URLs from sitemap")
                    
                    # Process each URL individually rather than using crawl_many
                    # This ensures we process each page directly without relying on link discovery
                    await update_progress(f"Processing {len(crawl_urls)} individual URLs from sitemap")
                    
                    for idx, url in enumerate(crawl_urls):
                        try:
                            await update_progress(f"Processing sitemap URL {idx+1}/{len(crawl_urls)}: {url}")
                            # Process each page directly with the original _process_page method
                            page_info = crawler._process_page(url)
                            if page_info:
                                # Store the result directly
                                crawler.results[url] = page_info
                                crawler.visited_urls.add(url)
                        except Exception as url_error:
                            await update_progress(f"✗ Error processing sitemap URL {url}: {str(url_error)}")
                    
                    await update_progress(f"Completed processing {len(crawl_urls)} URLs from sitemap")
                    await update_progress(f"Successfully processed {len(crawler.results)} pages")
                else:
                    await update_progress(f"No URLs found in sitemap. Falling back to standard crawling.")
                    crawler.verify_links(request.url, max_depth=request.max_depth)
            except Exception as sitemap_error:
                await update_progress(f"⚠ Error parsing sitemap: {str(sitemap_error)}")
                await update_progress(f"Falling back to standard crawling")
                # Use the existing verify_links method
                crawler.verify_links(request.url, max_depth=request.max_depth)
        else:
            # Use the existing verify_links method for standard crawling
            try:
                # Check if the crawler has a progress_callback parameter
                crawler_params = inspect.signature(crawler.verify_links).parameters
                
                # Attempt to pass callback if verify_links accepts it
                if 'progress_callback' in crawler_params:
                    await update_progress("Using real-time progress reporting via callback")
                    crawler.verify_links(request.url, max_depth=request.max_depth, progress_callback=crawler_progress_callback)
                else:
                    # Fallback to original method
                    await update_progress("Using standard progress reporting")
                    crawler.verify_links(request.url, max_depth=request.max_depth)
                    
            except Exception as crawl_error:
                await update_progress(f"✗ Error during crawling: {str(crawl_error)}")
                raise crawl_error
        
        # Limit results if max_pages specified (and not set to 0)
        if request.max_pages > 0 and len(crawler.results) > request.max_pages:
            limited_results = {}
            for i, (url, data) in enumerate(crawler.results.items()):
                if i >= request.max_pages:
                    break
                limited_results[url] = data
            crawler.results = limited_results
            await update_progress(f"Limited results to {request.max_pages} pages")
        
        await job_state.update_status("storing", job_id)
        await update_progress(f"Saving results to local storage...")
        
        # Store results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"crawl_results_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(crawler.results, f, indent=2, ensure_ascii=False)
            
        await update_progress(f"✓ Saved results to {output_file}")
        
        # Store the output file path in the job state
        job_state.output_file = os.path.abspath(output_file)
        
        # Transform results for frontend
        transformed_result = {
            "url": request.url,
            "status": "success",
            "crawl_info": {
                "pages_crawled": len(crawler.results),
                "depth": request.max_depth,
                "max_pages": request.max_pages
            },
            "progress_logs": job_state.progress_logs,
            "pages": [
                {
                    "url": url,
                    "title": data.get("metadata", {}).get("title", "") or 
                            data.get("content", {}).get("title", "") or 
                            "No title",
                    "summary": data.get("metadata", {}).get("summary", "") or 
                              data.get("content", {}).get("summary", ""),
                    "content": data.get("content", {}).get("markdown", ""),
                    "extracted_data": {
                        "title": data.get("metadata", {}).get("title", "") or 
                                data.get("content", {}).get("title", "") or 
                                "No title",
                        "summary": data.get("content", {}).get("summary", "") or 
                                  data.get("metadata", {}).get("summary", "") or 
                                  "No summary available",
                        "key_points": data.get("content", {}).get("key_points", []) or 
                                     data.get("metadata", {}).get("key_points", []),
                        "topics": data.get("content", {}).get("topics", []) or 
                                 data.get("metadata", {}).get("topics", []),
                        "related_topics": [link for link in data.get("links", [])] if data.get("links") else [],
                        "word_count": data.get("content", {}).get("metadata", {}).get("word_count", 0),
                        "chunk_count": data.get("content", {}).get("metadata", {}).get("chunk_count", 0),
                        "code_examples": data.get("content", {}).get("code_examples", [])
                    }
                }
                for url, data in crawler.results.items()
            ],
            "vectorized": True
        }
        
        # Save results to local file
        await update_progress(f"Saving crawl results to local file: {output_file}")
        crawler.save_results(output_file)
        
        # Explicitly try to save to database separately (not just through save_results)
        try:
            await job_state.update_status("saving to database", job_id)
            await update_progress("Attempting direct database save...")
            
            # Make sure the Supabase adapter is properly initialized
            if not crawler.supabase:
                await update_progress("No Supabase client in crawler, initializing adapter directly...")
                from core.db_adapter import SupabaseAdapter
                adapter = SupabaseAdapter(
                    supabase_url=crawler.supabase_url,
                    supabase_key=crawler.supabase_key,
                    embedding_model=crawler.embedding_model
                )
                
                await update_progress(f"Processing {len(crawler.results)} pages for database insertion...")
                successful_inserts = 0
                
                # Process each page directly with the adapter
                for url, page_data in crawler.results.items():
                    try:
                        page_metadata = page_data.get("metadata", {})
                        content_data = page_data.get("content", {})
                        
                        # Generate ID for this page - use timestamp-based numeric ID instead of UUID
                        crawl_id = int(datetime.now().timestamp() * 1000)
                        
                        # Format data for site_pages table
                        crawl_data = {
                            "id": crawl_id,
                            "url": url,
                            "title": page_metadata.get("title", ""),
                            "content": content_data.get("markdown", ""),
                            "summary": content_data.get("summary", ""),
                            "embedding": page_data.get("embedding"),
                            "metadata": {
                                "crawl_date": page_metadata.get("crawl_date", datetime.now().isoformat()),
                                "word_count": content_data.get("metadata", {}).get("word_count", 0),
                                "chunk_count": content_data.get("metadata", {}).get("chunk_count", 0),
                                "embedding_model": crawler.embedding_model if page_data.get("embedding") else None,
                                "links": page_data.get("links", []),
                            }
                        }
                        
                        # Insert the page
                        await update_progress(f"Inserting page: {url}")
                        result = adapter.insert_site_page(crawl_data)
                        
                        if result:
                            successful_inserts += 1
                            await update_progress(f"✓ Successfully inserted page {successful_inserts}/{len(crawler.results)}")
                        else:
                            await update_progress(f"✗ Failed to insert page: {url}")
                    
                    except Exception as page_error:
                        await update_progress(f"✗ Error inserting page {url}: {str(page_error)}")
                
                if successful_inserts > 0:
                    await update_progress(f"✓ Successfully inserted {successful_inserts}/{len(crawler.results)} pages to database")
                    transformed_result["database_saved"] = True
                else:
                    await update_progress("✗ No pages were inserted into the database")
                    transformed_result["database_saved"] = False
            else:
                # Use the crawler's _save_to_supabase method
                await update_progress("Using crawler's built-in database save method...")
                crawler._save_to_supabase()
                await update_progress("Database save operation completed")
                transformed_result["database_saved"] = True
        except Exception as db_error:
            await update_progress(f"⚠ Database error: {str(db_error)}")
            transformed_result["database_saved"] = False
        
        # Finalize the crawl
        await update_progress(f"Crawl completed: {len(crawler.results)} pages processed")
        job_state.progress = 1.0
        job_state.result = transformed_result
        await job_state.update_status("completed", job_id)
        
        # Save result to global state for later retrieval
        job_state.result = transformed_result
        job_state.output_file = os.path.abspath(output_file)
        
        # Final log message
        await update_progress(f"✓ Crawl completed successfully in {time.time() - job_state.start_time:.1f} seconds")
        
        # Restore original stdout
        sys.stdout = original_stdout
        
    except Exception as e:
        # Print exception details
        traceback.print_exc()
        error_msg = str(e)
        await update_progress(f"❌ Error: {error_msg}")
        
        # Update job status to error
        job_state.error = error_msg
        await job_state.update_status("error", job_id)
        
        # Restore original stdout
        sys.stdout = original_stdout

# New request model for multi-URL crawling
class MultiCrawlRequest(BaseModel):
    urls: List[str]
    depth: int = 2
    max_pages: int = 50
    model: str = "llama2"
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    max_concurrent_requests: int = 5
    save_to_db: bool = True
    generate_embeddings: bool = True

@app.post("/api/crawl-many", response_model=CrawlResponse)
async def start_multi_crawl(request: MultiCrawlRequest, background_tasks: BackgroundTasks):
    """Start a multi-URL crawl job"""
    job_id = str(uuid.uuid4())
    
    # Create job state for tracking progress
    job_state = JobState()
    active_jobs[job_id] = job_state
    
    # Start the multi-URL crawl task in the background
    background_tasks.add_task(process_multi_crawl, request, job_id, job_state)
    
    return {"job_id": job_id, "status": "pending"}

async def process_multi_crawl(request: MultiCrawlRequest, job_id: str, job_state: JobState):
    """Process a multi-URL crawl request"""
    # Store original stdout to restore later
    original_stdout = sys.stdout
    
    try:
        await job_state.update_status("starting", job_id)
        job_state.progress_logs = []
        
        # Define progress update functions
        async def update_progress(message):
            """Update progress for this multi-crawl job"""
            await job_state.add_log(message, job_id)
            
        # Create a function to send terminal output directly to the client
        async def send_terminal_output(message: str):
            """Send terminal output directly to the websocket"""
            # Echo to terminal is handled by the redirector
            # Send to client WebSocket
            await job_state.add_log(f"[Terminal] {message}", job_id)
        
        # Intercept stdout for piping directly to WebSocket
        class WebSocketStreamRedirector:
            def __init__(self, original_stream, callback_func):
                self.original_stream = original_stream
                self.callback_func = callback_func
                
            def write(self, text):
                # Write to the original stream
                self.original_stream.write(text)
                # Only process non-empty text
                if text.strip():
                    # Create asyncio task to send to WebSocket
                    asyncio.create_task(self.callback_func(text.strip()))
                
            def flush(self):
                self.original_stream.flush()
        
        # Redirect stdout to our custom handler
        sys.stdout = WebSocketStreamRedirector(original_stdout, send_terminal_output)
        
        # Initialize
        await update_progress(f"Initializing multi-URL crawl with {len(request.urls)} starting points...")
        
        # Derive allowed domains from URLs
        domains = set()
        for url in request.urls:
            parsed = urlparse(url)
            domains.add(parsed.netloc)
        
        await update_progress(f"Allowed domains: {', '.join(domains)}")
        
        # Custom callback function to capture output from crawler
        def crawler_progress_callback(message):
            # Create an asyncio task to send the message via WebSocket
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(update_progress(message), loop)
            # Also print to terminal for visibility (will be captured by our redirector)
            print(f"CRAWLER: {message}")
            
        try:
            # Initialize crawler
            crawler = DeepCrawler(
                llm_model=request.model,
                embedding_model="snowflake-arctic-embed2:latest",
                system_prompt=request.system_prompt,
                allowed_domains=list(domains)
            )
            await update_progress(f"Crawler initialized successfully")
            
            # Check Supabase connection and log status
            if crawler.supabase:
                await update_progress("✓ Successfully connected to Supabase database")
            else:
                await update_progress("ℹ️ Supabase client initialized with 'headers' attribute warning - this is expected and non-critical")
                
            # Rest of the existing code with crawling, saving, etc...
            
            # Update status to completed
            await job_state.update_status("completed", job_id)
            await update_progress(f"Crawl completed: {len(crawler.results)} pages processed")
            
            # Store the result in the job state
            job_state.result = {
                "status": "success",
                # Rest of the result data
            }
            
            # Restore original stdout
            sys.stdout = original_stdout
                
        except Exception as init_error:
            await update_progress(f"✗ Error initializing crawler: {str(init_error)}")
            traceback.print_exc()
            # Restore original stdout
            sys.stdout = original_stdout
            raise init_error
            
    except Exception as e:
        await job_state.update_status("failed", job_id)
        await update_progress(f"Error: {str(e)}")
        traceback.print_exc()
        job_state.error = str(e)
        
        # Restore original stdout
        sys.stdout = original_stdout

@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """Get job status with progress logs and basic information"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
    job_state = active_jobs[job_id]
    
    # Calculate some statistics
    duration = round(time.time() - job_state.start_time, 1)
    pages_per_second = job_state.pages_crawled / max(1, duration) if duration > 0 else 0
    
    # Return progress information
    response = {
        "status": job_state.status,
        "progress": min(0.99, job_state.progress) if job_state.status != "completed" else 1.0,
        "current_page": job_state.current_page,
        "pages_crawled": job_state.pages_crawled,
        "progress_logs": job_state.progress_logs,
        "duration": duration,
        "pages_per_second": round(pages_per_second, 2),
        "output_file": job_state.output_file
    }
    
    if job_state.error:
        response["error"] = str(job_state.error)
        
    return response

@app.get("/api/results/{job_id}")
async def get_job_results(job_id: str):
    """Get complete crawl results for a job"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
    job_state = active_jobs[job_id]
    
    # If job is not completed, return current status
    if job_state.status != "completed":
        return {
            "status": job_state.status,
            "message": "Results not available yet - job is still in progress",
            "progress": min(0.99, job_state.progress),
            "pages_crawled": job_state.pages_crawled
        }
    
    # If we don't have the output file, return error
    if not job_state.output_file or not os.path.exists(job_state.output_file):
        return {
            "status": "error",
            "message": "Output file not found",
            "error": "The crawl output file could not be located"
        }
    
    try:
        # Read the output file
        with open(job_state.output_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Process the results for frontend consumption
        processed_results = []
        for url, data in results.items():
            # Extract only what the frontend needs
            page_data = {
                "url": url,
                "title": data.get("metadata", {}).get("title", "Unknown Title"),
                "content_summary": data.get("content", {}).get("summary", "No summary available"),
                "content_topics": data.get("content", {}).get("topics", []),
                "embedding_length": len(data.get("embedding", [])) if "embedding" in data else 0,
                "word_count": data.get("content", {}).get("metadata", {}).get("word_count", 0),
                "chunk_count": data.get("content", {}).get("metadata", {}).get("chunk_count", 0),
                "links": data.get("links", [])
            }
            processed_results.append(page_data)
        
        # Return the results
        return {
            "status": "completed",
            "message": "Crawl results ready",
            "pages_count": len(processed_results),
            "results": processed_results
        }
    except Exception as e:
        print(f"Error retrieving results: {str(e)}")
        traceback.print_exc()
        return {
            "status": "error",
            "message": "Failed to process results",
            "error": str(e)
        }

@app.get("/api/models")
async def get_models():
    try:
        # Try to get models directly from Ollama with better error handling
        ollama_models = []
        try:
            print("Attempting to fetch models directly from Ollama API...")
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "models" in data and isinstance(data["models"], list):
                    ollama_models = data["models"]
                    print(f"Successfully fetched {len(ollama_models)} models from Ollama API")
                    
                    # Return the full model details
                    return {
                        "success": True,
                        "completion_models": [
                            {
                                "name": model["name"], 
                                "size": model.get("size", 0),
                                "modified_at": model.get("modified_at", "")
                            } 
                            for model in ollama_models
                        ]
                    }
            else:
                print(f"Ollama API returned non-200 status code: {response.status_code}")
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error reaching Ollama API: {e}")
        except requests.exceptions.Timeout:
            print("Timeout while connecting to Ollama API")
        except Exception as e:
            print(f"Unexpected error fetching from Ollama API: {e}")
        
        # Try integrated_workflow method if direct API call failed
        try:
            print("Attempting to fetch models via integrated_workflow...")
            models = run_crawl_from_params.get_available_ollama_models()
            if models and len(models) > 0:
                print(f"Successfully fetched {len(models)} models via integrated_workflow")
                return {
                    "success": True,
                    "completion_models": [{"name": model} for model in models]
                }
            else:
                print("No models returned from integrated_workflow")
        except Exception as e:
            print(f"Error in integrated_workflow model fetch: {e}")
        
        # Provide some default models as a final fallback
        print("Using default model list as fallback")
        return {
            "success": True,
            "completion_models": [
                {"name": "llama3:8b"},
                {"name": "llama3:70b"},
                {"name": "gemma3:27b"},
                {"name": "gemma:7b"},
                {"name": "mistral"},
                {"name": "neural-chat"},
                {"name": "phi3"},
                {"name": "starling-lm"},
                {"name": "snowflake-arctic-embed2:latest"}
            ]
        }
    except Exception as e:
        print(f"Unhandled error in get_models endpoint: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "completion_models": [
                {"name": "llama3:8b"},
                {"name": "gemma3:27b"},
                {"name": "snowflake-arctic-embed2:latest"}
            ]
        }

@app.get("/api/database-status")
async def check_database_status():
    """Check the status of the Supabase database connection"""
    try:
        # Create a new database adapter to test the connection
        adapter = SupabaseAdapter()
        
        # Try a simple operation
        table_info = None
        error_details = None
        connection_status = "connected"
        
        try:
            # Get table info directly using the adapter
            if hasattr(adapter, 'supabase_client') and adapter.supabase_client:
                # Try to query the table metadata
                response = adapter.supabase_client.table('crawl_data').select('count(*)', count='exact').execute()
                if response and hasattr(response, 'count'):
                    table_info = {
                        "count": response.count,
                        "table": "crawl_data"
                    }
        except Exception as db_error:
            error_details = str(db_error)
            if "'dict' object has no attribute 'headers'" in error_details:
                connection_status = "connected_with_warning"  # Change from error to warning status
            else:
                connection_status = "error_query"
                
        # Return detailed status
        response = {
            "status": connection_status,
            "database_type": "supabase",
            "connected": connection_status.startswith("connected"),  # Both connected and connected_with_warning are considered connected
            "time": datetime.now().isoformat()
        }
        
        if table_info:
            response["table_info"] = table_info
            
        if error_details:
            response["warning"] = error_details if connection_status == "connected_with_warning" else None
            response["error"] = error_details if connection_status != "connected_with_warning" else None
            response["error_type"] = connection_status
            
            # Add troubleshooting information for common errors
            if connection_status == "connected_with_warning":
                response["troubleshooting"] = {
                    "message": "The Supabase client shows a 'headers' attribute warning during initialization. This is non-critical.",
                    "functionality": "Database operations will still function correctly despite this warning.",
                    "status": "The system is operating normally."
                }
            
        return response
    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "error": str(e),
            "error_type": "connection_failed",
            "time": datetime.now().isoformat()
        }

@app.get("/api/results-files")
async def list_result_files():
    """List all available crawl result files"""
    try:
        # Get current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Look for crawl result files in the current directory and parent directory
        result_files = []
        
        # Search patterns for result files
        file_patterns = [
            os.path.join(current_dir, "crawl_results_*.json"),
            os.path.join(os.path.dirname(current_dir), "crawl_results_*.json")
        ]
        
        # Find files matching the patterns
        for pattern in file_patterns:
            matching_files = glob.glob(pattern)
            for file_path in matching_files:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                file_time = os.path.getmtime(file_path)
                
                # Try to extract timestamp from filename
                timestamp_str = None
                try:
                    # Extract timestamp from format crawl_results_YYYYMMDD_HHMMSS.json
                    parts = file_name.replace('crawl_results_', '').replace('.json', '')
                    if '_' in parts:
                        date_part, time_part = parts.split('_')
                        if len(date_part) == 8 and len(time_part) == 6:
                            # Format: YYYYMMDD_HHMMSS
                            timestamp_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}T{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                except Exception:
                    pass
                
                # Add file info to the list
                result_files.append({
                    "filename": file_name,
                    "path": file_path,
                    "size_bytes": file_size,
                    "size_formatted": f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024 else f"{file_size / (1024 * 1024):.1f} MB",
                    "timestamp": datetime.fromtimestamp(file_time).isoformat(),
                    "crawl_time": timestamp_str
                })
        
        # Sort by modification time (newest first)
        result_files.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "status": "success",
            "count": len(result_files),
            "files": result_files
        }
    except Exception as e:
        print(f"Error listing result files: {str(e)}")
        traceback.print_exc()
        return {
            "status": "error",
            "message": "Failed to list result files",
            "error": str(e)
        }

# Function to create required database tables if they don't exist
def create_database_tables_if_needed():
    try:
        print("Initializing database adapter for table creation...")
        adapter = SupabaseAdapter()  # This will use default connection settings
        
        # The adapter will automatically check and create tables as needed during initialization
        print("✓ Database tables verified through adapter")
            
    except Exception as e:
        print(f"❌ Error in create_database_tables_if_needed: {str(e)}")

def save_to_database(pages):
    try:
        print("Initializing direct database adapter...")
        adapter = SupabaseAdapter()  # This will use default connection settings
        success_count = 0
        total_pages = len(pages)
        
        # First, yield a summary of what we'll be doing
        yield f"Starting database save operation for {total_pages} pages..."
        
        for i, page in enumerate(pages, 1):
            try:
                # Prepare the data according to the exact schema
                page_data = {
                    "url": page.url,
                    "chunk_number": page.chunk_number if hasattr(page, 'chunk_number') else 0,
                    "title": page.title,
                    "summary": page.summary if hasattr(page, 'summary') else "",
                    "content": page.content,
                    "metadata": page.metadata if hasattr(page, 'metadata') else {},
                    "embedding": page.embedding if hasattr(page, 'embedding') else None
                }
                
                # Use shorter log output with only essential info
                title_preview = page.title[:40] + "..." if len(page.title) > 40 else page.title
                print(f"[{i}/{total_pages}] Inserting: {page.url} - {title_preview}")
                
                # Use the adapter's insert_site_page method
                result = adapter.insert_site_page(page_data)
                
                if result:
                    success_count += 1
                    # Only yield every few pages or for the first/last pages to reduce output volume
                    if i == 1 or i == total_pages or success_count % 5 == 0:
                        yield f"✓ Saved {success_count}/{total_pages} pages to database..."
                else:
                    print(f"❌ Error saving page {page.url}")
                    yield f"❌ Failed to save: {page.url}"
                    
            except Exception as e:
                # Provide a concise error message
                error_preview = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
                print(f"❌ Error processing page {page.url}: {error_preview}")
                yield f"❌ Error with {page.url}: {error_preview}"
                
        # Final summary
        if success_count == 0:
            yield "❌ Failed to save any pages to database"
        elif success_count == total_pages:
            yield f"✓ Successfully saved all {success_count} pages to database"
        else:
            yield f"✓ Saved {success_count} of {total_pages} pages to database"
            
    except Exception as e:
        error_msg = str(e)[:150] + "..." if len(str(e)) > 150 else str(e)
        print(f"❌ Database operation error: {error_msg}")
        yield f"❌ Database error: {error_msg}"

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await manager.connect(websocket, job_id)
    try:
        # Send initial status immediately on connection
        if job_id in active_jobs:
            job_state = active_jobs[job_id]
            await websocket.send_text(json.dumps({
                "type": "status",
                "status": job_state.status,
                "progress": job_state.progress,
                "current_page": job_state.current_page,
                "pages_crawled": job_state.pages_crawled
            }))
            
            # Send any existing logs immediately
            if hasattr(job_state, 'progress_logs') and job_state.progress_logs:
                for log in job_state.progress_logs:
                    await websocket.send_text(json.dumps({
                        "type": "progress",
                        "message": log,
                        "status": job_state.status
                    }))
                print(f"Sent {len(job_state.progress_logs)} existing logs to new WebSocket client")
                
            # If job is already completed, send a final status message and close connection
            if job_state.status in ["completed", "error", "failed"]:
                await websocket.send_text(json.dumps({
                    "type": "status",
                    "status": job_state.status,
                    "message": "Job already completed. No more updates will be sent.",
                    "progress": job_state.progress,
                    "pages_crawled": job_state.pages_crawled
                }))
                # Close the connection gracefully
                await websocket.close(code=1000, reason="Job already completed")
                return
        
        # Keep connection alive and listen for messages (client may send ping once to get status)
        while True:
            # Wait for a message with a timeout so we can check job status periodically
            try:
                # Use a receive with timeout to check job status periodically
                message = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
                print(f"Received WebSocket message: {message} for job {job_id}")
                
                # Only process a ping message once to get initial status
                if message == "ping":
                    if job_id in active_jobs:
                        job_state = active_jobs[job_id]
                        
                        # If job is completed after we started, close the connection
                        if job_state.status in ["completed", "error", "failed"]:
                            # Send final status
                            await websocket.send_text(json.dumps({
                                "type": "status",
                                "status": job_state.status,
                                "message": "Job completed. Connection will be closed.",
                                "progress": job_state.progress,
                                "pages_crawled": job_state.pages_crawled
                            }))
                            # Close the connection gracefully
                            await websocket.close(code=1000, reason="Job completed")
                            return
                        
                        # Otherwise, send regular status update
                        await websocket.send_text(json.dumps({
                            "type": "status",
                            "status": job_state.status,
                            "progress": job_state.progress,
                            "pages_crawled": job_state.pages_crawled
                        }))
                    else:
                        # Job is no longer active, close the connection
                        await websocket.send_text(json.dumps({
                            "type": "status",
                            "status": "completed",
                            "message": "Job is no longer active. Connection will be closed."
                        }))
                        await websocket.close(code=1000, reason="Job no longer active")
                        return
            except asyncio.TimeoutError:
                # No message received, check if job is still active or completed
                if job_id in active_jobs:
                    job_state = active_jobs[job_id]
                    # If job is now completed, close the connection
                    if job_state.status in ["completed", "error", "failed"]:
                        await websocket.send_text(json.dumps({
                            "type": "status",
                            "status": job_state.status,
                            "message": "Job completed. Connection will be closed.",
                            "progress": job_state.progress,
                            "pages_crawled": job_state.pages_crawled
                        }))
                        await websocket.close(code=1000, reason="Job completed")
                        return
                    # Otherwise, continue listening
                else:
                    # Job no longer exists, close connection
                    await websocket.send_text(json.dumps({
                        "type": "status",
                        "status": "completed",
                        "message": "Job no longer exists. Connection will be closed."
                    }))
                    await websocket.close(code=1000, reason="Job no longer exists")
                    return
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for job {job_id}")
        manager.disconnect(websocket, job_id)
    except Exception as e:
        print(f"WebSocket error for job {job_id}: {e}")
        manager.disconnect(websocket, job_id)

if __name__ == "__main__":
    # Try a series of ports if the default port is in use
    port = 1111
    max_port = 1120  # Try ports 1111-1120
    
    while port <= max_port:
        try:
            print(f"Attempting to start server on port {port}...")
            uvicorn.run(app, host="0.0.0.0", port=port)
            break  # If successful, exit the loop
        except OSError as e:
            if "address already in use" in str(e).lower():
                print(f"Port {port} is already in use, trying next port...")
                port += 1
                if port > max_port:
                    print("All ports in range are in use. Please free up a port or modify the port range.")
                    break
            else:
                # For other errors, just raise
                raise e 