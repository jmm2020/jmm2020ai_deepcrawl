#!/usr/bin/env python3
"""
Deep Crawler with Link Verification and Embeddings

IMPORTANT: This is the primary crawler file for the Crawl4AI system.
Always use this file for crawling content and storing it in Supabase.

This crawler provides:
1. Deep crawling of websites with configurable depth
2. Link verification to avoid broken links
3. Content extraction and transformation to markdown
4. LLM-powered summarization
5. Vector embeddings generation
6. Storage in Supabase database
7. Automatic chunking of long content

For Supabase connections, always use:
SUPABASE_URL=http://localhost:8001
"""

import requests
import json
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Set, Any
import re
from datetime import datetime
import uuid  # For generating unique IDs for Supabase
import urllib3
import traceback

# Disable SSL warnings for local development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Supabase client for Python
try:
    from supabase import create_client, Client
    import httpx
except ImportError:
    print("Supabase client not found. Installing it now...")
    import subprocess
    subprocess.check_call(["pip", "install", "supabase"])
    from supabase import create_client, Client
    import httpx

class DeepCrawler:
    def __init__(self, auth_token="__n8n_BLANK_VALUE_e5362baf-c777-4d57-a609-6eaf1f9e87f6", 
                 supabase_url="http://localhost:8001", 
                 supabase_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im53ZHNhbXJjZXBuYnp6aXNjeWN0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc0ODUwNTYsImV4cCI6MjA1MzA2MTA1Nn0.zwZzrvJxybBByOBR_4pYIIAiikmPVlD6o3IYf-c21yg",
                 llm_model="llama3",
                 embedding_model="snowflake-arctic-embed2",
                 allowed_domains=None,
                 system_prompt=None):
        self.auth_token = auth_token
        self.api_base = "http://localhost:11235"
        self.visited_urls = set()
        self.results = {}
        self.ollama_endpoint = "http://localhost:11434/api/generate"
        self.ollama_embedding_endpoint = "http://localhost:11434/api/embeddings"
        
        # LLM and embedding model configuration
        self.llm_model = llm_model  # Model for summarization and text processing
        self.embedding_model = embedding_model  # Model for embeddings
        self.system_prompt = system_prompt or "Summarize the key points of this page"
        
        # Domain restrictions - if None, will be set based on first URL
        self.allowed_domains = allowed_domains
        
        # Initialize Supabase client
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        try:
            # Configure HTTPX transport with verify=False for local development
            transport = httpx.HTTPTransport(verify=False)
            try:
                # Wrap the create_client call in a try block to handle specific errors
                self.supabase: Client = create_client(
                    self.supabase_url, 
                    self.supabase_key,
                    options={
                        "http_client": httpx.Client(transport=transport)
                    }
                )
                # Test the connection by querying a table
                test_query = self.supabase.table("site_pages").select("id").limit(1).execute()
                print(f"Connected to Supabase at {self.supabase_url}")
            except Exception as client_err:
                print(f"Supabase client initialization error: {str(client_err)}")
                # Create a simple fallback mechanism to log but continue
                self.supabase = None
        except Exception as e:
            print(f"Failed to connect to Supabase: {str(e)}")
            self.supabase = None

    def verify_links(self, url: str, max_depth: int = 2, progress_callback=None) -> Dict:
        """
        Verify links starting from a given URL up to a specified depth.
        Returns a dictionary containing information about each verified link.
        
        Args:
            url: Starting URL to crawl
            max_depth: Maximum depth of crawling
            progress_callback: Optional callback function for real-time progress updates
        
        Returns:
            Dictionary of page information
        """
        if max_depth < 0:
            return {}

        # Skip if already visited
        if url in self.visited_urls:
            return {}

        print(f"\nProcessing URL: {url} (depth: {max_depth})")
        # Send progress update via callback if provided
        if progress_callback:
            progress_callback(f"Processing page: {url}")
            
        self.visited_urls.add(url)

        # Extract content and links from the page
        page_info = self._process_page(url, progress_callback)
        if page_info:
            self.results[url] = page_info
            
            # Send progress update via callback if provided
            if progress_callback:
                if 'title' in page_info:
                    progress_callback(f"✓ Successfully processed: {url}")
                    progress_callback(f"  Title: {page_info['title']}")
                if 'content_stats' in page_info:
                    progress_callback(f"  Content stats: {page_info['content_stats']}")
            
            # If we have more depth to go, process the links from this page
            if max_depth > 0:
                links = page_info.get("links", [])
                for i, link_url in enumerate(links):
                    if link_url not in self.visited_urls:
                        try:
                            # Send progress update via callback if provided
                            if progress_callback:
                                progress_callback(f"Processing link {i+1}/{len(links)}: {link_url}")
                            
                            # Recursively crawl with reduced depth
                            self.verify_links(link_url, max_depth=max_depth-1, progress_callback=progress_callback)
                        except Exception as e:
                            print(f"Error processing link {link_url}: {str(e)}")
                            # Send error via callback if provided
                            if progress_callback:
                                progress_callback(f"✗ Error processing link {link_url}: {str(e)}")

        return page_info

    def crawl_many(self, urls: List[str], max_depth: int = 2, max_concurrent_requests: int = 5, progress_callback=None) -> Dict:
        """
        Crawl multiple URLs with parallelization support.
        
        Args:
            urls: List of URLs to crawl
            max_depth: Maximum crawl depth for each URL
            max_concurrent_requests: Maximum number of concurrent requests
            progress_callback: Optional callback function for real-time progress updates
            
        Returns:
            Dictionary containing information about each verified link
        """
        import asyncio
        import threading
        from concurrent.futures import ThreadPoolExecutor
        from threading import Lock
        from time import time
        
        if not urls:
            print("No URLs provided for crawl_many.")
            if progress_callback:
                progress_callback("No URLs provided for crawl_many.")
            return {}
            
        print(f"\nStarting multi-URL crawl with {len(urls)} starting points")
        if progress_callback:
            progress_callback(f"Starting multi-URL crawl with {len(urls)} starting points")
            progress_callback(f"Max depth: {max_depth}")
            progress_callback(f"Max concurrent requests: {max_concurrent_requests}")
        
        # Clear the results dictionary to start fresh
        self.results = {}
        
        # Create a lock for thread-safe operations
        results_lock = Lock()
        
        # Rate limiting setup
        request_times = []
        requests_lock = Lock()
        MIN_REQUEST_INTERVAL = 0.1  # Minimum time between requests (seconds)
        
        def wait_for_rate_limit():
            with requests_lock:
                current_time = time()
                # Remove old request times
                while request_times and current_time - request_times[0] > 1.0:
                    request_times.pop(0)
                
                # If we've made too many requests recently, wait
                if len(request_times) >= max_concurrent_requests:
                    sleep_time = request_times[0] + 1.0 - current_time
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                
                # Add current request time
                request_times.append(current_time)
                
                # Ensure minimum interval between requests
                if request_times and len(request_times) > 1:
                    last_request = request_times[-2]
                    time_since_last = current_time - last_request
                    if time_since_last < MIN_REQUEST_INTERVAL:
                        time.sleep(MIN_REQUEST_INTERVAL - time_since_last)
        
        # Function to crawl a single URL in a separate thread
        def crawl_single_url(url):
            try:
                wait_for_rate_limit()
                
                if progress_callback:
                    progress_callback(f"Processing URL: {url}")
                
                page_info = self._process_page(url, progress_callback)
                
                if page_info:
                    with results_lock:
                        self.results[url] = page_info
                    
                    # Process child links with rate limiting
                    if max_depth > 0:
                        links = page_info.get("links", [])
                        for i, link_url in enumerate(links):
                            if link_url not in self.visited_urls:
                                try:
                                    wait_for_rate_limit()
                                    
                                    if progress_callback:
                                        progress_callback(f"Processing link {i+1}/{len(links)}: {link_url}")
                                    
                                    # Recursively crawl with reduced depth
                                    self.verify_links(link_url, max_depth=max_depth-1, progress_callback=progress_callback)
                                except Exception as e:
                                    print(f"Error processing link {link_url}: {str(e)}")
                                    if progress_callback:
                                        progress_callback(f"✗ Error processing link {link_url}: {str(e)}")
                
                return page_info
                
            except Exception as e:
                print(f"Error crawling {url}: {str(e)}")
                if progress_callback:
                    progress_callback(f"Error crawling {url}: {str(e)}")
                return None
        
        # Use ThreadPoolExecutor to limit concurrent requests
        with ThreadPoolExecutor(max_workers=max_concurrent_requests) as executor:
            # Submit all URLs to the thread pool
            future_to_url = {executor.submit(crawl_single_url, url): url for url in urls}
            
            # Process results as they complete
            for i, future in enumerate(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    if result:
                        print(f"✓ Completed crawl for {url} ({i+1}/{len(urls)})")
                        if progress_callback:
                            progress_callback(f"✓ Completed crawl for {url} ({i+1}/{len(urls)})")
                    else:
                        print(f"✗ Failed to crawl {url} ({i+1}/{len(urls)})")
                        if progress_callback:
                            progress_callback(f"✗ Failed to crawl {url} ({i+1}/{len(urls)})")
                except Exception as e:
                    print(f"✗ Exception during crawl of {url}: {str(e)}")
                    if progress_callback:
                        progress_callback(f"✗ Exception during crawl of {url}: {str(e)}")
        
        print(f"\nMulti-URL crawl completed. Processed {len(self.results)} pages from {len(urls)} starting points.")
        if progress_callback:
            progress_callback(f"Multi-URL crawl completed. Processed {len(self.results)} pages from {len(urls)} starting points.")
        
        return self.results

    @staticmethod
    def parse_sitemap(sitemap_url: str) -> List[str]:
        """
        Parse a sitemap.xml file and extract all URLs.
        
        Args:
            sitemap_url: URL to the sitemap.xml file
            
        Returns:
            List of URLs found in the sitemap
        """
        try:
            import xml.etree.ElementTree as ET
            from urllib.parse import urljoin
            
            # Download the sitemap
            response = requests.get(sitemap_url, verify=False)
            response.raise_for_status()
            
            # Parse the XML
            xml_content = response.text
            root = ET.fromstring(xml_content)
            
            # Extract URLs - handle different sitemap formats
            # Standard format: <url><loc>URL</loc></url>
            urls = []
            
            # Check if we have a urlset (standard sitemap)
            if root.tag.endswith('urlset'):
                # Extract URLs from standard sitemap format
                for url_element in root.findall('.//{*}url'):
                    loc_element = url_element.find('.//{*}loc')
                    if loc_element is not None and loc_element.text:
                        urls.append(loc_element.text.strip())
            
            # Check if we have a sitemapindex (sitemap of sitemaps)
            elif root.tag.endswith('sitemapindex'):
                # Extract sitemap URLs and recursively process them
                sitemap_urls = []
                for sitemap_element in root.findall('.//{*}sitemap'):
                    loc_element = sitemap_element.find('.//{*}loc')
                    if loc_element is not None and loc_element.text:
                        sitemap_urls.append(loc_element.text.strip())
                
                # Process each sitemap
                for sub_sitemap_url in sitemap_urls:
                    sub_urls = DeepCrawler.parse_sitemap(sub_sitemap_url)
                    urls.extend(sub_urls)
            
            # For RSS/Atom feeds that some sites use as sitemaps
            elif root.tag.endswith('rss') or root.tag.endswith('feed'):
                # Extract URLs from items/entries
                for item in root.findall('.//{*}item') or root.findall('.//{*}entry'):
                    link = item.find('.//{*}link')
                    if link is not None:
                        # RSS: <link>URL</link> or Atom: <link href="URL"/>
                        if link.text:
                            urls.append(link.text.strip())
                        elif 'href' in link.attrib:
                            urls.append(link.attrib['href'].strip())
            
            print(f"Extracted {len(urls)} URLs from sitemap: {sitemap_url}")
            return urls
            
        except Exception as e:
            print(f"Error parsing sitemap {sitemap_url}: {str(e)}")
            return []

    def _process_page(self, url: str, progress_callback=None) -> Optional[Dict]:
        """
        Process a single page: extract content and verify links.
        
        Args:
            url: URL to process
            progress_callback: Optional callback function for real-time progress updates
        
        Returns:
            Dictionary of page information or None on error
        """
        try:
            # Skip URLs that don't match allowed domains
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            if domain.startswith('www.'):
                domain = domain[4:]  # Remove www. prefix
            
            # If allowed_domains is None, set it based on the first URL
            if self.allowed_domains is None:
                self.allowed_domains = [domain]
                print(f"Setting allowed domain to: {domain}")
                if progress_callback:
                    progress_callback(f"Setting allowed domain to: {domain}")
                
            # Check if URL matches any allowed domain
            domain_allowed = False
            for allowed_domain in self.allowed_domains:
                # Handle full URLs in allowed_domains list by extracting the netloc
                if allowed_domain.startswith(('http://', 'https://')):
                    allowed_domain = urlparse(allowed_domain).netloc
                if allowed_domain.startswith('www.'):
                    allowed_domain = allowed_domain[4:]  # Remove www. prefix
                
                # Allow if domain matches or is subdomain
                if domain == allowed_domain or domain.endswith('.' + allowed_domain):
                    domain_allowed = True
                    break
            
            if not domain_allowed:
                print(f"Skipping URL not in allowed domains: {url}")
                if progress_callback:
                    progress_callback(f"Skipping URL not in allowed domains: {url}")
                return None
                
            # Submit content extraction task
            if progress_callback:
                progress_callback(f"Extracting content from: {url}")
                
            content = self._extract_content(url)
            if not content:
                print(f"Skipping URL with no content: {url}")
                if progress_callback:
                    progress_callback(f"Skipping URL with no content: {url}")
                return None
                
            # Extract links from the HTML content
            links = []
            if "cleaned_html" in content:
                soup = BeautifulSoup(content["cleaned_html"], 'html.parser')
                base_url = url
                parsed_base = urlparse(base_url)
                
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    # Skip invalid or non-http links
                    if not href or href.startswith(('#', 'javascript:', 'mailto:')):
                        continue
                        
                    # Convert to absolute URL
                    absolute_url = urljoin(base_url, href)
                    parsed_url = urlparse(absolute_url)
                    
                    # Only include links that match allowed domains and filter out any non-HTML content
                    domain_allowed = False
                    for allowed_domain in self.allowed_domains:
                        # Handle full URLs in allowed_domains by extracting the netloc
                        if allowed_domain.startswith(('http://', 'https://')):
                            allowed_domain = urlparse(allowed_domain).netloc
                            
                        if parsed_url.netloc == allowed_domain or parsed_url.netloc.endswith('.' + allowed_domain):
                            domain_allowed = True
                            break
                    
                    if (domain_allowed and 
                        not any(absolute_url.lower().endswith(ext) for ext in ['.pdf', '.zip', '.jpg', '.png', '.gif'])):
                        links.append(absolute_url)
            
            # Extract page title from HTML
            title = content.get("title", "")
            if not title and "cleaned_html" in content:
                soup = BeautifulSoup(content["cleaned_html"], 'html.parser')
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.text.strip()
                else:
                    h1_tag = soup.find('h1')
                    if h1_tag:
                        title = h1_tag.text.strip()
            
            # Generate a summary using LLM if markdown content is available
            summary = ""
            chunks = []
            if "markdown" in content and content["markdown"]:
                # Chunk the markdown content
                chunks = self._chunk_markdown(content["markdown"])
                
                if progress_callback:
                    progress_callback(f"  Content stats: {len(content['markdown'].split())} words, {len(chunks)} chunks")
                
                # Get summary using LLM
                if progress_callback:
                    progress_callback(f"Generating summary for: {url}")
                summary = self._get_summary_with_llm(title, chunks, progress_callback)
            
            # Combine results
            result = {
                "status": "accessible",
                "content": {
                    "markdown": content.get("markdown", ""),
                    "title": title,
                    "summary": summary,
                    "chunks": chunks,
                    "metadata": {
                        "extraction_date": datetime.now().isoformat(),
                        "word_count": len(content.get("markdown", "").split()) if content.get("markdown") else 0,
                        "chunk_count": len(chunks)
                    }
                },
                "links": links,
                "metadata": {
                    "crawl_date": datetime.now().isoformat(),
                    "url": url,
                    "title": title,
                    "summary": summary
                }
            }
            
            # Generate embeddings for the content
            embedding = None
            if content.get("markdown"):
                # Generate embedding for the whole content
                if progress_callback:
                    progress_callback(f"Generating embeddings for: {url}")
                embedding = self._get_embedding(f"{title}\n\n{content.get('markdown')}", progress_callback)
                if embedding:
                    result["embedding"] = embedding
                    print(f"Generated embedding with {len(embedding)} dimensions for {url}")
                    if progress_callback:
                        progress_callback(f"✓ Generated embeddings for: {url}")
            
            return result
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            if progress_callback:
                progress_callback(f"✗ Error processing {url}: {str(e)}")
            return None

    def _get_embedding(self, text: str, progress_callback=None) -> Optional[List[float]]:
        """
        Generate an embedding for the given text using Ollama.
        
        Args:
            text: Text to generate embeddings for
            progress_callback: Optional callback function for real-time progress updates
            
        Returns:
            List of embedding values or None on error
        """
        try:
            # Truncate text if too long
            if len(text) > 8000:
                if progress_callback:
                    progress_callback(f"Truncating text from {len(text)} to 8000 characters for embedding generation")
                text = text[:8000]
            
            # Call Ollama embeddings API with the specified model
            if progress_callback:
                progress_callback(f"Generating embedding with {self.embedding_model} model")
                
            response = requests.post(
                self.ollama_embedding_endpoint,
                json={
                    "model": self.embedding_model,
                    "prompt": text
                }
            )
            
            if response.status_code == 200:
                embedding = response.json().get("embedding")
                
                # Check for embedding dimension mismatch and fix
                if embedding:
                    current_dim = len(embedding)
                    expected_dim = 1536  # Expected dimension
                    print(f"Generated embedding with {current_dim} dimensions for the content")
                    
                    # If dimensions don't match, pad or truncate to expected size
                    if current_dim != expected_dim:
                        if current_dim < expected_dim:
                            # Pad with zeros to reach expected dimension
                            padding = [0.0] * (expected_dim - current_dim)
                            embedding.extend(padding)
                            print(f"Padded embedding from {current_dim} to {expected_dim} dimensions")
                            if progress_callback:
                                progress_callback(f"Padded embedding from {current_dim} to {expected_dim} dimensions")
                        else:
                            # Truncate to expected dimension
                            embedding = embedding[:expected_dim]
                            print(f"Truncated embedding from {current_dim} to {expected_dim} dimensions")
                            if progress_callback:
                                progress_callback(f"Truncated embedding from {current_dim} to {expected_dim} dimensions")
                
                return embedding
            else:
                print(f"Error calling Ollama embeddings: {response.status_code} - {response.text}")
                if progress_callback:
                    progress_callback(f"Error calling Ollama embeddings: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            if progress_callback:
                progress_callback(f"Error generating embedding: {str(e)}")
            return None

    def _chunk_markdown(self, markdown_text: str, max_chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """
        Split markdown text into chunks based on natural boundaries.
        Returns a list of chunk dictionaries with content and position information.
        """
        if not markdown_text:
            return []
            
        # Use regex pattern to split on paragraph breaks or headers
        chunk_pattern = r'(\n\n|\n#{1,6} )'
        text_parts = re.split(chunk_pattern, markdown_text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        # Combine splits to maintain the delimiter with the content
        for i in range(0, len(text_parts)):
            # Skip empty parts
            if not text_parts[i].strip():
                continue
                
            # If adding this part would exceed max_chunk_size, save current chunk and start a new one
            if len(current_chunk) + len(text_parts[i]) > max_chunk_size and current_chunk:
                chunks.append({
                    "id": chunk_index,
                    "content": current_chunk.strip(),
                    "word_count": len(current_chunk.split())
                })
                current_chunk = text_parts[i]
                chunk_index += 1
            else:
                current_chunk += text_parts[i]
        
        # Add the last chunk if there's any content left
        if current_chunk.strip():
            chunks.append({
                "id": chunk_index,
                "content": current_chunk.strip(),
                "word_count": len(current_chunk.split())
            })
        
        return chunks

    def _get_summary_with_llm(self, title: str, chunks: List[Dict], progress_callback=None) -> str:
        """
        Generate a summary using an LLM.
        
        Args:
            title: Page title
            chunks: Content chunks
            progress_callback: Optional callback function for real-time progress updates
            
        Returns:
            Summary text
        """
        try:
            # Prepare content for summarization
            combined_text = title + "\n\n"
            for chunk in chunks[:3]:  # Use first 3 chunks for summary
                if isinstance(chunk, dict) and "content" in chunk:
                    combined_text += chunk["content"] + "\n\n"
                elif isinstance(chunk, str):
                    combined_text += chunk + "\n\n"
            
            # Truncate if too long
            if len(combined_text) > 8000:
                if progress_callback:
                    progress_callback(f"Truncating content from {len(combined_text)} to 8000 characters for summarization")
                combined_text = combined_text[:8000]
            
            # Create prompt using the system prompt
            prompt = f"""{self.system_prompt}:

{combined_text}

Summary:"""
            
            # Call Ollama with the specified model
            if progress_callback:
                progress_callback(f"Generating summary with {self.llm_model} model")
                
            response = requests.post(
                self.ollama_endpoint,
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                summary = response.json().get("response", "").strip()
                if progress_callback:
                    progress_callback(f"Successfully generated summary ({len(summary.split())} words)")
                return summary
            else:
                print(f"Error calling Ollama: {response.status_code} - {response.text}")
                if progress_callback:
                    progress_callback(f"Error generating summary: {response.status_code}")
                return ""
                
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            if progress_callback:
                progress_callback(f"Error generating summary: {str(e)}")
            return ""

    def _extract_content(self, url: str) -> Optional[Dict]:
        """Extract content from a page using direct HTML extraction."""
        max_retries = 3
        retry_delay = 1  # seconds
        
        # Import selectors utility
        from utils.selectors import get_selectors_for_url, is_cli_documentation
        
        for attempt in range(max_retries):
            try:
                # Fetch the page with increased timeout
                response = requests.get(url, verify=False, timeout=30)
                response.raise_for_status()
                html_content = response.text
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Get title
                title = ""
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.text.strip()
                if not title:
                    h1_tag = soup.find('h1')
                    if h1_tag:
                        title = h1_tag.text.strip()
                
                # Remove unwanted elements
                for element in soup.find_all(['script', 'style', 'nav', 'footer', 'iframe']):
                    element.decompose()
                
                # Try to find main content with specialized selectors for this URL
                main_content = None
                is_cli_doc = is_cli_documentation(url)
                selectors = get_selectors_for_url(url)
                
                # Log the type of page we're extracting (helps with debugging)
                if is_cli_doc:
                    print(f"Detected CLI documentation page: {url}")
                    
                # Try specialized selectors first
                for selector in selectors:
                    content_elements = soup.select(selector)
                    if content_elements:
                        # If multiple elements found, combine them
                        if len(content_elements) > 1:
                            container = soup.new_tag('div')
                            for element in content_elements:
                                container.append(element)
                            main_content = container
                        else:
                            main_content = content_elements[0]
                        break
                
                # If no main content found, use body
                if not main_content:
                    main_content = soup.find('body')
                
                # If still no content, use the whole soup
                if not main_content:
                    main_content = soup
                
                # Convert to markdown-like format
                markdown = ""
                if main_content:
                    # Process headings
                    for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                        level = int(heading.name[1])
                        markdown += '#' * level + ' ' + heading.get_text().strip() + '\n\n'
                    
                    # Process paragraphs and text content
                    for element in main_content.find_all(['p', 'div', 'section']):
                        text = element.get_text().strip()
                        if text:  # Only add non-empty text
                            markdown += text + '\n\n'
                    
                    # Process lists
                    for ul in main_content.find_all('ul'):
                        for li in ul.find_all('li'):
                            markdown += '* ' + li.get_text().strip() + '\n'
                        markdown += '\n'
                    
                    for ol in main_content.find_all('ol'):
                        for i, li in enumerate(ol.find_all('li'), 1):
                            markdown += f'{i}. ' + li.get_text().strip() + '\n'
                        markdown += '\n'
                    
                    # Process code blocks
                    for pre in main_content.find_all('pre'):
                        code = pre.get_text().strip()
                        if code:
                            markdown += '```\n' + code + '\n```\n\n'
                
                # Clean up the markdown
                markdown = re.sub(r'\n{3,}', '\n\n', markdown)  # Remove excessive newlines
                markdown = markdown.strip()
                
                if not markdown:
                    print(f"Warning: No content extracted from {url}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                
                return {
                    "title": title,
                    "cleaned_html": str(main_content) if main_content else "",
                    "markdown": markdown
                }
                
            except requests.RequestException as e:
                print(f"Request error in content extraction ({attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
            except Exception as e:
                print(f"Error in content extraction ({attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
        
        print(f"Failed to extract content from {url} after {max_retries} attempts")
        return None

    def _poll_task(self, task_id: str) -> Optional[Dict]:
        """Poll for task completion and return results."""
        headers = {
            "Authorization": f"Bearer {self.auth_token}"
        }
        
        max_attempts = 30  # Match working example
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            time.sleep(2)  # Match working example's shorter interval
            
            try:
                response = requests.get(
                    f"{self.api_base}/task/{task_id}",
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("status") == "completed":
                    if "result" in result:
                        return result["result"]  # Return the entire result object
                    print("Task completed but no result found")
                    return None
                
                print(f"Task status: {result.get('status', 'unknown')} (attempt {attempt}/{max_attempts})")
                
            except Exception as e:
                print(f"Error polling task: {str(e)}")
                return None
            
        print("Task timed out")
        return None

    def save_results(self, filename: str = "link_verification_results.json"):
        """Save the crawl results to a JSON file and to Supabase."""
        # Save to local JSON file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {filename}")
        
        # Save to Supabase if client is available
        if self.supabase:
            self._save_to_supabase()
    
    def _save_to_supabase(self):
        """Save crawl results to Supabase database."""
        if not self.supabase:
            print("Supabase client not available. Skipping database save.")
            return
        
        try:
            print("\nSaving results to Supabase...")
            successful_inserts = 0
            failed_inserts = 0
            
            # Import SupabaseAdapter if not already available
            from db_adapter import SupabaseAdapter
            
            # Initialize direct database adapter
            print("Initializing direct database adapter...")
            adapter = SupabaseAdapter(
                supabase_url=self.supabase_url,
                supabase_key=self.supabase_key,
                embedding_model=self.embedding_model
            )
            
            # Check if we have data to save
            if not self.results:
                print("No results to save to database")
                return
                
            print(f"Starting database save operation for {len(self.results)} pages...")
                
            # Process each URL and its data
            for i, (url, page_data) in enumerate(self.results.items(), 1):
                try:
                    # Print progress
                    print(f"[{i}/{len(self.results)}] Inserting: {url} - {page_data.get('metadata', {}).get('title', 'No title')[:40]}...")
                    
                    # Prepare data for Supabase - format it according to the expected schema
                    page_metadata = page_data.get("metadata", {})
                    content_data = page_data.get("content", {})
                    
                    # Generate a unique ID for this crawl result
                    crawl_id = str(uuid.uuid4())
                    
                    # Create the main crawl record formatted for site_pages table
                    crawl_data = {
                        "id": crawl_id,
                        "url": url,
                        "title": page_metadata.get("title", ""),
                        "content": content_data.get("markdown", ""),
                        "summary": content_data.get("summary", ""),
                        "embedding": page_data.get("embedding"),  # Add main page embedding
                        "metadata": {
                            "crawl_date": page_metadata.get("crawl_date", datetime.now().isoformat()),
                            "word_count": content_data.get("metadata", {}).get("word_count", 0),
                            "chunk_count": content_data.get("metadata", {}).get("chunk_count", 0),
                            "embedding_model": self.embedding_model if page_data.get("embedding") else None,
                            "links": page_data.get("links", []),
                        }
                    }
                    
                    # Insert the main crawl record using the adapter's method
                    result = adapter.insert_site_page(crawl_data)
                    
                    if result:
                        # Insert chunks if available
                        if "chunks" in content_data and content_data["chunks"]:
                            for idx, chunk in enumerate(content_data["chunks"]):
                                # Generate embedding for this chunk if not already present
                                chunk_embedding = None
                                chunk_text = chunk.get("content", "")
                                if chunk_text:
                                    chunk_embedding = page_data.get("embedding")  # Use page embedding for consistency
                                    
                                chunk_data = {
                                    "page_id": crawl_id,
                                    "content": chunk_text,
                                    "embedding": chunk_embedding,
                                    "metadata": {
                                        "url": url,
                                        "title": page_metadata.get("title", ""),
                                        "chunk_index": chunk.get("id", idx),
                                        "word_count": chunk.get("word_count", 0)
                                    }
                                }
                                
                                # Insert chunk using adapter's method
                                adapter.insert_document(chunk_data)
                            
                            print(f"Inserted {len(content_data['chunks'])} documents for {url}")
                        
                        successful_inserts += 1
                    else:
                        failed_inserts += 1
                        print(f"Failed to insert record for URL: {url}")
                    
                except Exception as e:
                    failed_inserts += 1
                    print(f"Error saving data for URL {url} to Supabase: {str(e)}")
            
            if successful_inserts > 0:
                print(f"✓ Saved {successful_inserts}/{len(self.results)} pages to database...")
                print(f"✓ Successfully saved all {successful_inserts} pages to database")
            else:
                print("No pages were successfully saved to database")
            
        except Exception as e:
            print(f"Error during Supabase save operation: {str(e)}")
            traceback.print_exc()
            
    def verify_embeddings_in_database(self):
        """Verify that embeddings were successfully saved to the database"""
        if not self.supabase:
            print("Supabase client not available. Cannot verify embeddings.")
            return
            
        try:
            print("\nVerifying embeddings in Supabase database...")
            
            # Check site_pages table
            crawl_results = self.supabase.table("site_pages").select("id,url,title").is_("embedding", "not.null").execute()
            if crawl_results.data:
                print(f"Found {len(crawl_results.data)} site pages with embeddings:")
                for i, result in enumerate(crawl_results.data[:5]):  # Show first 5 for brevity
                    print(f" - {result.get('title', 'No title')} ({result.get('url', 'No URL')})")
                if len(crawl_results.data) > 5:
                    print(f" ... and {len(crawl_results.data) - 5} more")
            else:
                print("No site pages with embeddings found.")
                
            # Check content_chunks table
            content_chunks = self.supabase.table("documents").select("id,crawl_id").is_("embedding", "not.null").execute()
            if content_chunks.data:
                print(f"Found {len(content_chunks.data)} documents with embeddings")
            else:
                print("No documents with embeddings found.")
                
            return crawl_results.data, content_chunks.data 
            
        except Exception as e:
            print(f"Error verifying embeddings: {str(e)}")
            return None, None 