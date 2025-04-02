#!/usr/bin/env python3
"""
Integrated Workflow for Crawl4AI

This script demonstrates the complete workflow:
1. Crawl a website using DeepCrawler from master_crawl.py
2. Save the crawl results to a JSON file
3. Load the crawl results into Supabase using SupabaseAdapter

Usage:
    python integrated_workflow.py --url URL [--depth DEPTH] [--max_pages MAX_PAGES] [--llm_model MODEL]

Example:
    python integrated_workflow.py --url https://example.com --depth 2 --max_pages 10 --llm_model llama3
"""

import argparse
import json
import os
import sys
import time
import traceback
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Add parent directory to path to resolve imports
sys.path.append(str(Path(__file__).parent.parent))

# Update imports for new directory structure
from core.master_crawl import DeepCrawler
from utils.paths import get_results_path

# Import SupabaseAdapter from db_adapter.py
from core.db_adapter import SupabaseAdapter


def pad_embedding(embedding, target_dimensions=1536):
    """Pad an embedding to the target dimensions by repeating values."""
    current_dimensions = len(embedding)
    
    if current_dimensions == target_dimensions:
        return embedding
    
    if current_dimensions > target_dimensions:
        return embedding[:target_dimensions]
    
    # Pad by repeating the embedding
    padding_repeats = (target_dimensions // current_dimensions) + 1
    padded_embedding = (embedding * padding_repeats)[:target_dimensions]
    
    print(f"Padded embedding from {current_dimensions} to {target_dimensions} dimensions")
    return padded_embedding


def get_available_ollama_models():
    """Get list of available models from Ollama API."""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = [model["name"] for model in response.json().get("models", [])]
            return models
        return ["llama3", "phi3", "mistral", "falcon"]  # Default models if API call fails
    except Exception as e:
        print(f"Error fetching Ollama models: {e}")
        return ["llama3", "phi3", "mistral", "falcon"]  # Fallback models


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Integrated Crawl4AI workflow")
    
    # Main crawling parameters
    parser.add_argument("--url", type=str, required=True, help="URL to crawl")
    parser.add_argument("--depth", type=int, default=2, help="Crawl depth (default: 2)")
    parser.add_argument("--max_pages", type=int, default=10, help="Maximum pages to crawl (default: 10)")
    
    # LLM and embedding model parameters
    parser.add_argument("--llm_model", type=str, default="llama3", help="Ollama LLM model for summarization")
    parser.add_argument("--embedding_model", type=str, default="snowflake-arctic-embed2", 
                        help="Embedding model (default: snowflake-arctic-embed2)")
    parser.add_argument("--system_prompt", type=str, default="Summarize the key technical information on this page", 
                       help="System prompt for LLM (default: Summarize the key technical information on this page)")
    
    # Domain restriction parameters
    parser.add_argument("--allowed_domains", type=str, nargs="+", 
                        help="List of allowed domains to crawl (default: derived from URL)")
    
    # Output parameters
    parser.add_argument("--output", type=str, default=None, 
                       help="Output JSON file path (default: crawl_results_TIMESTAMP.json)")
    parser.add_argument("--skip-db", action="store_true", help="Skip database insertion")
    
    return parser.parse_args()


def main():
    """Run the integrated workflow."""
    args = parse_arguments()
    
    # Generate output filename with timestamp if not provided
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"crawl_results_{timestamp}.json"
    
    # Derive allowed domains from URL if not specified
    if not args.allowed_domains:
        from urllib.parse import urlparse
        parsed_url = urlparse(args.url)
        args.allowed_domains = [parsed_url.netloc]
    
    print(f"\n{'='*80}")
    print(f"INTEGRATED CRAWL4AI WORKFLOW")
    print(f"{'='*80}")
    print(f"URL: {args.url}")
    print(f"Depth: {args.depth}")
    print(f"Max Pages: {args.max_pages if args.max_pages > 0 else 'Unlimited'}")
    print(f"LLM Model: {args.llm_model}")
    print(f"Embedding Model: {args.embedding_model}")
    print(f"Allowed Domains: {', '.join(args.allowed_domains)}")
    print(f"Output: {args.output}")
    print(f"Skip Database: {args.skip_db}")
    print(f"{'='*80}\n")
    
    # STEP 1: Crawl the website using DeepCrawler
    print(f"\n{'='*30}")
    print(f"[STEP 1] CRAWLING WEBSITE")
    print(f"{'='*30}")
    print(f"Target URL: {args.url}")
    print(f"Depth: {args.depth}")
    print(f"Max Pages: {args.max_pages}")
    print(f"LLM Model: {args.llm_model}")
    print(f"Starting crawl at {datetime.now().strftime('%H:%M:%S')}")
    
    start_time = time.time()
    
    # Pass LLM and embedding model as parameters to DeepCrawler
    crawler = DeepCrawler(
        llm_model=args.llm_model,
        embedding_model=args.embedding_model,
        allowed_domains=args.allowed_domains,
        system_prompt=args.system_prompt
    )
    crawler.verify_links(args.url, max_depth=args.depth)
    
    # Limit to max_pages if specified and greater than 0
    if args.max_pages > 0 and len(crawler.results) > args.max_pages:
        print(f"Limiting results to {args.max_pages} pages (crawled {len(crawler.results)} pages)")
        # Keep the first max_pages results
        limited_results = {}
        for i, (url, data) in enumerate(crawler.results.items()):
            if i >= args.max_pages:
                break
            limited_results[url] = data
        crawler.results = limited_results
    else:
        print(f"Processing all {len(crawler.results)} crawled pages")
    
    crawl_time = time.time() - start_time
    print(f"Crawl completed in {crawl_time:.2f} seconds")
    print(f"Crawled {len(crawler.results)} pages")
    
    # STEP 2: Save the crawl results to a JSON file
    print(f"\n{'='*30}")
    print(f"[STEP 2] SAVING RESULTS")
    print(f"{'='*30}")
    print(f"Output file: {args.output}")
    
    save_start_time = time.time()
    
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(crawler.results, f, indent=2, ensure_ascii=False)
        
        save_time = time.time() - save_start_time
        print(f"✓ Results saved in {save_time:.2f} seconds")
        print(f"✓ File size: {os.path.getsize(args.output) / (1024 * 1024):.2f} MB")
    except Exception as e:
        print(f"✗ Error saving results: {str(e)}")
        return
    
    # STEP 3: Load the crawl results into Supabase (if not skipped)
    db_time = 0
    successful_inserts = 0
    failed_inserts = 0
    
    if not args.skip_db:
        print(f"\n{'='*30}")
        print(f"[STEP 3] DATABASE OPERATIONS")
        print(f"{'='*30}")
        print(f"Starting database insertion at {datetime.now().strftime('%H:%M:%S')}")
        
        db_start_time = time.time()
        
        # Initialize the adapter
        try:
            adapter = SupabaseAdapter(
                embedding_model=args.embedding_model,
                embedding_dimensions=1536  # Fixed at 1536 for consistent embeddings
            )
            
            # Log count of pages to be processed
            total_pages = len(crawler.results)
            print(f"Inserting {total_pages} pages into database...")
            
            # Process each crawled page
            for i, (url, page_data) in enumerate(crawler.results.items(), 1):
                try:
                    # Print progress count
                    print(f"[{i}/{total_pages}] Processing: {url}")
                    
                    # Get content and metadata from the crawl results
                    content = page_data.get("content", {})
                    metadata = page_data.get("metadata", {})
                    
                    # Pad embedding to correct dimensions if needed
                    if "embedding" in page_data:
                        page_data["embedding"] = pad_embedding(page_data["embedding"], 1536)
                    
                    # Prepare site_page data for main page (chunk_number = 1)
                    site_page = {
                        "url": url,
                        "chunk_number": 1,  # Main page is always chunk 1
                        "title": metadata.get("title", "No Title"),
                        "summary": metadata.get("summary", ""),
                        "content": content.get("markdown", ""),
                        "metadata": metadata,
                        "created_at": datetime.now().isoformat()
                    }
                    
                    # Add embedding if available
                    if "embedding" in page_data:
                        site_page["embedding"] = page_data["embedding"]
                    
                    # Insert into site_pages
                    print("Inserting main page into site_pages table...")
                    inserted_page = adapter.insert_site_page(site_page)
                    
                    if not inserted_page:
                        print(f"Failed to insert site_page for {url}")
                        failed_inserts += 1
                        continue
                    
                    page_id = inserted_page.get("id")
                    print(f"Inserted site_page with ID: {page_id}")
                    
                    # Process chunks if available - add them as additional rows in site_pages
                    chunks = content.get("chunks", [])
                    if chunks:
                        print(f"Processing {len(chunks)} chunks...")
                        
                        for i, chunk_data in enumerate(chunks):
                            try:
                                # Extract chunk content from the chunk structure
                                chunk_content = chunk_data.get("content", "")
                                if not chunk_content and isinstance(chunk_data, str):
                                    chunk_content = chunk_data
                                
                                # Create a modified URL for chunks to ensure unique URL+chunk_number
                                chunk_url = f"{url}#chunk_{i+1}"
                                chunk_number = i + 2  # Main page is 1, chunks start at 2
                                
                                # Generate embedding for the chunk
                                chunk_text = f"{site_page['title']}\n\n{chunk_content}"
                                chunk_embedding = adapter.generate_embedding(chunk_text)
                                
                                # Pad the embedding to correct dimensions
                                if chunk_embedding:
                                    chunk_embedding = pad_embedding(chunk_embedding, 1536)
                                
                                # Prepare explicit chunk data with all required fields
                                chunk_page = {
                                    "id": int(time.time() * 1000) + i + 1,  # Ensure unique ID
                                    "url": chunk_url,
                                    "chunk_number": chunk_number,
                                    "title": f"{site_page['title'] if site_page['title'] else 'Content'} - Chunk {i+1}",
                                    "summary": site_page['summary'],
                                    "content": chunk_content,
                                    "metadata": {
                                        "parent_url": url,
                                        "parent_id": page_id,
                                        "chunk_index": i,
                                        "source_url": url,
                                        "crawl_date": datetime.now().isoformat()
                                    },
                                    "embedding": chunk_embedding,
                                    "created_at": datetime.now().isoformat()
                                }
                                
                                # Try direct insertion using a custom SQL approach
                                try:
                                    print(f"  Inserting chunk {i+1}/{len(chunks)} with chunk_number {chunk_number}...")
                                    
                                    # Insert using standard adapter method first
                                    inserted_chunk = adapter.insert_site_page(chunk_page)
                                    
                                    if inserted_chunk:
                                        print(f"  Inserted chunk {i+1}/{len(chunks)} as site_page with ID {inserted_chunk.get('id')}")
                                    else:
                                        print(f"  Failed to insert chunk {i+1}/{len(chunks)}")
                                except Exception as e:
                                    print(f"  Error inserting chunk via adapter: {str(e)}")
                                    
                            except Exception as e:
                                print(f"  Error processing chunk {i+1}: {str(e)}")
                    
                    successful_inserts += 1
                    
                except Exception as e:
                    print(f"Error processing {url}: {str(e)}")
                    failed_inserts += 1
            
            db_time = time.time() - db_start_time
            print(f"\nSupabase loading completed in {db_time:.2f} seconds")
            print(f"Successfully inserted {successful_inserts} pages")
            print(f"Failed to insert {failed_inserts} pages")
            
        except Exception as e:
            print(f"Error initializing SupabaseAdapter: {str(e)}")
            print("Skipping database insertion")
    else:
        print("\n[STEP 3] Skipping database insertion as requested")
    
    # Print summary
    total_time = time.time() - start_time
    print(f"\n{'='*80}")
    print(f"WORKFLOW SUMMARY")
    print(f"{'='*80}")
    print(f"Total pages crawled: {len(crawler.results)}")
    if not args.skip_db:
        print(f"Pages saved to Supabase: {successful_inserts}")
    print(f"Crawl time: {crawl_time:.2f} seconds")
    print(f"Save to file time: {save_time:.2f} seconds")
    if not args.skip_db:
        print(f"Database load time: {db_time:.2f} seconds")
    print(f"Total workflow time: {total_time:.2f} seconds")
    print(f"{'='*80}")


# Function to list available Ollama models for GUI integration
def get_available_models_for_gui():
    """Return available models in a format suitable for GUI dropdown."""
    models = get_available_ollama_models()
    return {
        "llm_models": models,
        "embedding_models": ["snowflake-arctic-embed2", "nomic-embed-text"]
    }


# Add these functions to be called from GUI later
def run_crawl_from_params(params):
    """
    Run the crawl workflow with the given parameters.
    This function can be called directly from a GUI.
    
    Args:
        params: Dictionary with the following keys:
            - url: Target URL to crawl
            - depth: Crawl depth
            - max_pages: Maximum pages to crawl
            - llm_model: Ollama model for LLM operations
            - embedding_model: Model for embeddings
            - allowed_domains: List of allowed domains
            - system_prompt: Custom prompt for LLM (optional)
            - output: Output file path
            - skip_db: Whether to skip database insertion
    
    Returns:
        Dictionary with crawl results and statistics
    """
    # Create an object with attributes matching the expected args
    class Args:
        pass
    
    args = Args()
    args.url = params.get("url")
    args.depth = params.get("depth", 2)
    args.max_pages = params.get("max_pages", 10)
    args.llm_model = params.get("llm_model", "llama3")
    args.embedding_model = params.get("embedding_model", "snowflake-arctic-embed2")
    args.allowed_domains = params.get("allowed_domains", [])
    args.system_prompt = params.get("system_prompt", "Summarize the key points of this page")
    args.output = params.get("output")
    args.skip_db = params.get("skip_db", False)
    
    # Generate output filename with timestamp if not provided
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"crawl_results_{timestamp}.json"
    
    # Derive allowed domains from URL if not specified
    if not args.allowed_domains:
        from urllib.parse import urlparse
        parsed_url = urlparse(args.url)
        args.allowed_domains = [parsed_url.netloc]
    
    start_time = time.time()
    
    # Initialize crawler with parameters
    crawler = DeepCrawler(
        llm_model=args.llm_model,
        embedding_model=args.embedding_model,
        allowed_domains=args.allowed_domains,
        system_prompt=args.system_prompt
    )
    
    # Log the parameters for debugging
    print(f"Running with parameters:")
    print(f"  URL: {args.url}")
    print(f"  Depth: {args.depth}")
    print(f"  Allowed domains: {args.allowed_domains}")
    print(f"  LLM model: {args.llm_model}")
    print(f"  Embedding model: {args.embedding_model}")
    
    # Run the crawl
    crawler.verify_links(args.url, max_depth=args.depth)
    
    # Limit results if needed
    if args.max_pages > 0 and len(crawler.results) > args.max_pages:
        limited_results = {}
        for i, (url, data) in enumerate(crawler.results.items()):
            if i >= args.max_pages:
                break
            limited_results[url] = data
        crawler.results = limited_results
    
    # Save results to file
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(crawler.results, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving results: {str(e)}")
    
    # Insert into database if not skipped
    if not args.skip_db:
        adapter = SupabaseAdapter(
            embedding_model=args.embedding_model,
            embedding_dimensions=1536  # Fixed at 1536 for consistent embeddings
        )
        for url, page_data in crawler.results.items():
            try:
                # Process content and metadata
                content = page_data.get("content", {})
                metadata = page_data.get("metadata", {})
                
                # Pad embedding if needed
                if "embedding" in page_data:
                    page_data["embedding"] = pad_embedding(page_data["embedding"], 1536)
                
                # Prepare site_page data
                site_page = {
                    "url": url,
                    "chunk_number": 1,
                    "title": metadata.get("title", "No Title"),
                    "summary": metadata.get("summary", ""),
                    "content": content.get("markdown", ""),
                    "metadata": metadata,
                    "created_at": datetime.now().isoformat()
                }
                
                if "embedding" in page_data:
                    site_page["embedding"] = page_data["embedding"]
                
                # Insert into database
                adapter.insert_site_page(site_page)
                
                # Process chunks if available
                # (This part would be similar to the existing chunk processing code)
            except Exception as e:
                print(f"Error inserting {url}: {str(e)}")
    
    # Return statistics
    end_time = time.time()
    return {
        "status": "success",
        "pages_crawled": len(crawler.results),
        "execution_time": end_time - start_time,
        "output_file": args.output
    }


def run_multi_url_crawl(params):
    """
    Run a multi-URL crawl with the given parameters.
    
    Args:
        params: Dictionary with the following keys:
            - urls: List of URLs to crawl (required)
            - depth: Crawl depth for each URL (default: 2)
            - max_pages: Maximum pages to crawl in total (default: 50)
            - llm_model: Ollama model for LLM operations (default: llama3)
            - embedding_model: Model for embeddings (default: snowflake-arctic-embed2)
            - allowed_domains: List of allowed domains (optional)
            - system_prompt: Custom prompt for LLM (optional)
            - output: Output file path (optional)
            - max_concurrent_requests: Max concurrent requests (default: 5)
            - skip_db: Whether to skip database insertion (default: False)
    
    Returns:
        Dictionary with crawl results and statistics
    """
    # Validate required parameters
    if "urls" not in params or not params["urls"]:
        return {
            "status": "error",
            "message": "No URLs provided. The 'urls' parameter is required."
        }
    
    # Process parameters
    urls = params.get("urls", [])
    depth = params.get("depth", 2)
    max_pages = params.get("max_pages", 50)
    llm_model = params.get("llm_model", "llama3")
    embedding_model = params.get("embedding_model", "snowflake-arctic-embed2")
    allowed_domains = params.get("allowed_domains", [])
    system_prompt = params.get("system_prompt", "Summarize the key points of this page")
    output = params.get("output")
    max_concurrent_requests = params.get("max_concurrent_requests", 5)
    skip_db = params.get("skip_db", False)
    
    # Generate output filename with timestamp if not provided
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"multi_crawl_results_{timestamp}.json"
    
    # Derive allowed domains from URLs if not specified
    if not allowed_domains:
        from urllib.parse import urlparse
        domains = set()
        for url in urls:
            parsed_url = urlparse(url)
            domains.add(parsed_url.netloc)
        allowed_domains = list(domains)
    
    # Log parameters
    print(f"Running multi-URL crawl with parameters:")
    print(f"  URLs: {len(urls)} URLs provided")
    print(f"  Depth: {depth}")
    print(f"  Max pages: {max_pages}")
    print(f"  Allowed domains: {allowed_domains}")
    print(f"  Max concurrent requests: {max_concurrent_requests}")
    
    start_time = time.time()
    
    # Initialize crawler with parameters
    crawler = DeepCrawler(
        llm_model=llm_model,
        embedding_model=embedding_model,
        allowed_domains=allowed_domains,
        system_prompt=system_prompt
    )
    
    # Run multi-URL crawl
    crawler.crawl_many(urls, max_depth=depth, max_concurrent_requests=max_concurrent_requests)
    
    # Limit results if max_pages is specified
    if max_pages > 0 and len(crawler.results) > max_pages:
        print(f"Limiting results to {max_pages} pages (crawled {len(crawler.results)} pages)")
        limited_results = {}
        for i, (url, data) in enumerate(crawler.results.items()):
            if i >= max_pages:
                break
            limited_results[url] = data
        crawler.results = limited_results
    
    # Save results to file
    try:
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(crawler.results, f, indent=2, ensure_ascii=False)
        print(f"✓ Results saved to {output}")
    except Exception as e:
        print(f"Error saving results: {str(e)}")
    
    # Insert into database if not skipped
    db_successful = True
    if not skip_db:
        try:
            adapter = SupabaseAdapter(
                embedding_model=embedding_model,
                embedding_dimensions=1536
            )
            
            for url, page_data in crawler.results.items():
                try:
                    # Process content and metadata
                    content = page_data.get("content", {})
                    metadata = page_data.get("metadata", {})
                    
                    # Pad embedding if needed
                    if "embedding" in page_data:
                        page_data["embedding"] = pad_embedding(page_data["embedding"], 1536)
                    
                    # Prepare site_page data
                    site_page = {
                        "url": url,
                        "chunk_number": 1,
                        "title": metadata.get("title", "No Title"),
                        "summary": metadata.get("summary", ""),
                        "content": content.get("markdown", ""),
                        "metadata": metadata,
                        "created_at": datetime.now().isoformat()
                    }
                    
                    if "embedding" in page_data:
                        site_page["embedding"] = page_data["embedding"]
                    
                    # Insert into database
                    adapter.insert_site_page(site_page)
                except Exception as e:
                    print(f"Error inserting {url}: {str(e)}")
        except Exception as e:
            print(f"Database error: {str(e)}")
            db_successful = False
    
    # Return statistics
    end_time = time.time()
    return {
        "status": "success",
        "pages_crawled": len(crawler.results),
        "starting_urls": len(urls),
        "execution_time": end_time - start_time,
        "output_file": output,
        "database_saved": db_successful if not skip_db else "skipped",
        "allowed_domains": allowed_domains
    }


if __name__ == "__main__":
    main() 