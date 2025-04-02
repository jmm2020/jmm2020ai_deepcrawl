#!/usr/bin/env python3
"""
Post-Processing Script for Crawl4AI JSON Results

This script loads crawl result JSON files and inserts them into Supabase.
It's designed for use when the initial database insertion fails during crawling.

Usage:
    python process_json_to_supabase.py --input results.json [--batch_size 10]

Example:
    python process_json_to_supabase.py --input crawl_results_20250402_123456.json --batch_size 20
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import requests

# Add parent directory to path to resolve imports
sys.path.append(str(Path(__file__).parent.parent))

# Import from core modules
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

def process_json_file(input_file: str, batch_size: int = 10, retry_count: int = 3, delay_between_batches: float = 1.0):
    """
    Process a JSON file containing crawl results and insert them into Supabase.
    
    Args:
        input_file: Path to the JSON file
        batch_size: Number of records to process in each batch
        retry_count: Number of retries for failed insertions
        delay_between_batches: Delay in seconds between processing batches
    
    Returns:
        Tuple of (successful_count, failed_count)
    """
    print(f"\n{'='*80}")
    print(f"PROCESSING JSON FILE: {input_file}")
    print(f"{'='*80}")
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        return 0, 0
    
    # Load the JSON file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Successfully loaded {len(data)} records from {input_file}")
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return 0, 0
    
    # Initialize the Supabase adapter
    try:
        adapter = SupabaseAdapter(embedding_model="snowflake-arctic-embed2", embedding_dimensions=1536)
        print("Successfully initialized Supabase adapter")
    except Exception as e:
        print(f"Error initializing Supabase adapter: {e}")
        return 0, 0
    
    # Create log directory
    log_dir = Path(Path(__file__).parent.parent, "logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"supabase_import_{timestamp}.log"
    
    # Initialize counters
    successful_inserts = 0
    failed_inserts = 0
    skipped_duplicates = 0
    
    # Process the records in batches
    urls = list(data.keys())
    total_urls = len(urls)
    
    print(f"Processing {total_urls} URLs in batches of {batch_size}")
    print(f"Log file: {log_file}")
    
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write(f"Processing {input_file} at {datetime.now().isoformat()}\n")
        log.write(f"Total records: {total_urls}\n\n")
        
        # Check for existing records to avoid duplicates
        print("Checking for existing records in database...")
        existing_urls = check_existing_urls(adapter, urls)
        if existing_urls:
            print(f"Found {len(existing_urls)} existing URLs in the database")
            log.write(f"Found {len(existing_urls)} existing URLs in the database\n")
        
        for i in range(0, total_urls, batch_size):
            batch_urls = urls[i:i+batch_size]
            print(f"\nProcessing batch {i//batch_size + 1}/{(total_urls + batch_size - 1)//batch_size}")
            print(f"URLs {i+1}-{min(i+batch_size, total_urls)} of {total_urls}")
            
            for url in batch_urls:
                # Skip if URL already exists in database
                if url in existing_urls:
                    print(f"⚠ Skipping duplicate URL: {url}")
                    log.write(f"⚠ SKIPPED: {url} - Already exists in database\n")
                    skipped_duplicates += 1
                    continue
                
                page_data = data[url]
                try:
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
                    
                    # Try to insert with retries
                    inserted = False
                    for attempt in range(retry_count):
                        try:
                            print(f"Inserting {url} (attempt {attempt+1}/{retry_count})")
                            inserted_page = adapter.insert_site_page(site_page)
                            
                            if inserted_page:
                                page_id = inserted_page.get("id")
                                print(f"✓ Successfully inserted {url} with ID {page_id}")
                                log.write(f"✓ SUCCESS: {url} (ID: {page_id})\n")
                                successful_inserts += 1
                                inserted = True
                                # Add to existing URLs to prevent duplicates within this run
                                existing_urls.add(url)
                                break
                            else:
                                print(f"Insertion attempt {attempt+1} failed")
                        except Exception as insert_err:
                            print(f"Error during insertion attempt {attempt+1}: {str(insert_err)}")
                            time.sleep(1)  # Short delay before retry
                    
                    if not inserted:
                        print(f"✗ Failed to insert {url} after {retry_count} attempts")
                        log.write(f"✗ FAILED: {url} - Could not insert after {retry_count} attempts\n")
                        failed_inserts += 1
                    
                    # Process chunks if available (only if main page was inserted successfully)
                    if inserted and "chunks" in content:
                        chunks = content["chunks"]
                        print(f"Processing {len(chunks)} chunks for {url}")
                        
                        for chunk_idx, chunk in enumerate(chunks, 1):
                            try:
                                chunk_url = f"{url}#chunk{chunk_idx}"
                                # Skip if chunk URL already exists
                                if chunk_url in existing_urls:
                                    print(f"  ⚠ Skipping duplicate chunk: {chunk_idx}")
                                    continue
                                    
                                chunk_page = {
                                    "url": chunk_url,
                                    "chunk_number": chunk_idx + 1,  # +1 because main page is chunk 1
                                    "title": f"{site_page['title']} (Chunk {chunk_idx})",
                                    "content": chunk.get("content", ""),
                                    "metadata": {
                                        "parent_url": url,
                                        "chunk_index": chunk_idx,
                                        "total_chunks": len(chunks)
                                    },
                                    "created_at": datetime.now().isoformat(),
                                    "parent_id": page_id
                                }
                                
                                # Try to insert the chunk
                                chunk_page_id = adapter.insert_site_page(chunk_page)
                                if chunk_page_id:
                                    print(f"  ✓ Inserted chunk {chunk_idx}/{len(chunks)}")
                                    # Add to existing URLs to prevent duplicates within this run
                                    existing_urls.add(chunk_url)
                                else:
                                    print(f"  ✗ Failed to insert chunk {chunk_idx}")
                            except Exception as chunk_err:
                                print(f"  ✗ Error processing chunk {chunk_idx}: {str(chunk_err)}")
                
                except Exception as e:
                    print(f"✗ Error processing {url}: {str(e)}")
                    log.write(f"✗ ERROR: {url} - {str(e)}\n")
                    failed_inserts += 1
            
            # Delay between batches to avoid overwhelming the database
            if i + batch_size < total_urls:
                print(f"Waiting {delay_between_batches} seconds before next batch...")
                time.sleep(delay_between_batches)
            
            # Write progress to log
            log.write(f"\nBatch {i//batch_size + 1} completed at {datetime.now().isoformat()}\n")
            log.write(f"Running totals: {successful_inserts} successful, {failed_inserts} failed, {skipped_duplicates} skipped\n\n")
            
            # Print batch summary
            print(f"Batch {i//batch_size + 1} completed: {successful_inserts} successful, {failed_inserts} failed, {skipped_duplicates} skipped")
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"PROCESSING COMPLETE")
    print(f"{'='*80}")
    print(f"Total URLs processed: {total_urls}")
    print(f"Successfully inserted: {successful_inserts}")
    print(f"Failed to insert: {failed_inserts}")
    print(f"Skipped duplicates: {skipped_duplicates}")
    print(f"Success rate: {successful_inserts/(total_urls-skipped_duplicates)*100:.2f}% (excluding skipped)")
    print(f"Log file: {log_file}")
    
    return successful_inserts, failed_inserts

def check_existing_urls(adapter, urls):
    """
    Check which URLs already exist in the database to avoid duplicates
    
    Args:
        adapter: Initialized SupabaseAdapter
        urls: List of URLs to check
        
    Returns:
        Set of URLs that already exist in the database
    """
    existing_urls = set()
    
    try:
        # Use direct access to check URLs
        url = f"{adapter.supabase_url}/rest/v1/site_pages?select=url"
        headers = {
            "apikey": adapter.supabase_key,
            "Authorization": f"Bearer {adapter.supabase_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, verify=False)
        
        if response.status_code in (200, 206):
            db_records = response.json()
            db_urls = {record.get("url") for record in db_records if record.get("url")}
            
            # Find intersection with our URL list
            existing_urls = set(urls) & db_urls
            
            print(f"Found {len(db_urls)} total URLs in database")
            print(f"Found {len(existing_urls)} URLs from this import already in database")
            
        else:
            print(f"Error checking existing URLs: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception when checking existing URLs: {str(e)}")
    
    return existing_urls

def main():
    """Parse arguments and run the main process."""
    parser = argparse.ArgumentParser(description="Process Crawl4AI JSON results into Supabase")
    
    parser.add_argument("--input", type=str, required=True, help="Input JSON file path")
    parser.add_argument("--batch_size", type=int, default=10, help="Number of records to process in each batch")
    parser.add_argument("--retry_count", type=int, default=3, help="Number of retries for failed insertions")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay in seconds between processing batches")
    
    args = parser.parse_args()
    
    # Process the file
    successful, failed = process_json_file(
        args.input, 
        batch_size=args.batch_size,
        retry_count=args.retry_count,
        delay_between_batches=args.delay
    )
    
    # Return exit code based on success
    if failed == 0:
        return 0
    elif successful > 0:
        return 1  # Partial success
    else:
        return 2  # Complete failure

if __name__ == "__main__":
    sys.exit(main()) 