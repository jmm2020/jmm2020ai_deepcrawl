# Code Standards

Last Updated: **April 2, 2024**

## Overview

This document outlines the coding standards for the Crawl4AI project. It provides detailed guidelines for code organization, naming conventions, error handling, logging, and security practices.

## Code Organization

### Project Structure

The project follows this directory structure:

```
workbench/
├── api/              # API server implementation
├── core/             # Core crawler functionality
├── docs/             # Documentation
├── frontend/         # React-based frontend
├── scripts/          # Utility scripts
├── selectors/        # HTML selectors for different sites
├── tests/            # Test suite
├── utils/            # Utility functions
└── config/           # Configuration files
```

### Module Organization

Each Python module should be organized as follows:

1. Module docstring describing the module's purpose
2. Imports (standard library, third-party, local)
3. Constants
4. Exception classes
5. Helper functions
6. Main classes
7. Main functions
8. Module-level code (if any)

Example:
```python
"""
This module provides utilities for URL processing and validation.
"""

# Standard library imports
import re
import urllib.parse

# Third-party imports
import requests
from bs4 import BeautifulSoup

# Local imports
from utils.logging import get_logger

# Constants
URL_REGEX = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
MAX_URL_LENGTH = 2048

# Exception classes
class InvalidURLError(Exception):
    """Raised when a URL is invalid."""
    pass

# Helper functions
def _normalize_path(path):
    """Normalize a URL path by removing redundant slashes and resolving relative references."""
    # Implementation

# Main classes
class URLProcessor:
    """A class for processing and validating URLs."""
    # Implementation

# Main functions
def validate_url(url):
    """Validate a URL string."""
    # Implementation

def extract_domain(url):
    """Extract the domain from a URL."""
    # Implementation
```

## Naming Conventions

### Python

1. **Variables and Functions**: Use `snake_case` for variables and functions.
   ```python
   user_agent = "Mozilla/5.0"
   def extract_content(html):
       # Implementation
   ```

2. **Classes**: Use `PascalCase` for class names.
   ```python
   class ContentExtractor:
       # Implementation
   ```

3. **Constants**: Use `UPPER_SNAKE_CASE` for constants.
   ```python
   MAX_RETRY_COUNT = 3
   DEFAULT_TIMEOUT = 30
   ```

4. **Private Members**: Prefix private methods and variables with a single underscore.
   ```python
   def _internal_helper(self):
       # Implementation
   ```

5. **Special Methods**: Use double underscores for special methods.
   ```python
   def __init__(self):
       # Implementation
   ```

### JavaScript/TypeScript

1. **Variables and Functions**: Use `camelCase` for variables and functions.
   ```javascript
   const userAgent = "Mozilla/5.0";
   function extractContent(html) {
       // Implementation
   }
   ```

2. **Classes and Components**: Use `PascalCase` for class and component names.
   ```javascript
   class ContentExtractor {
       // Implementation
   }
   
   function CrawlerForm() {
       // Implementation
   }
   ```

3. **Constants**: Use `UPPER_SNAKE_CASE` for constants.
   ```javascript
   const MAX_RETRY_COUNT = 3;
   const DEFAULT_TIMEOUT = 30;
   ```

4. **Private Members**: Prefix private methods and variables with an underscore.
   ```javascript
   _internalHelper() {
       // Implementation
   }
   ```

5. **Interfaces and Types**: Use `PascalCase` for interfaces and types in TypeScript.
   ```typescript
   interface CrawlOptions {
       depth: number;
       timeout: number;
   }
   
   type CrawlResult = {
       url: string;
       content: string;
   };
   ```

## Code Documentation

### Python Docstrings

Use Google-style docstrings for Python code:

```python
def extract_links(html, base_url=None):
    """
    Extract all links from an HTML document.
    
    Args:
        html (str): The HTML content to parse.
        base_url (str, optional): The base URL to resolve relative links.
            Defaults to None.
    
    Returns:
        list: A list of extracted and normalized links.
    
    Raises:
        ValueError: If the HTML cannot be parsed.
    
    Examples:
        >>> extract_links("<a href='/page'>Page</a>", "https://example.com")
        ['https://example.com/page']
    """
    # Implementation
```

### JavaScript/TypeScript JSDoc

Use JSDoc comments for JavaScript/TypeScript code:

```javascript
/**
 * Extract all links from an HTML document.
 * 
 * @param {string} html - The HTML content to parse.
 * @param {string} [baseUrl] - The base URL to resolve relative links.
 * @returns {Array<string>} A list of extracted and normalized links.
 * @throws {Error} If the HTML cannot be parsed.
 * 
 * @example
 * extractLinks("<a href='/page'>Page</a>", "https://example.com")
 * // Returns: ['https://example.com/page']
 */
function extractLinks(html, baseUrl) {
    // Implementation
}
```

## Error Handling

### Python Error Handling

1. **Use Specific Exceptions**: Raise and catch specific exceptions rather than generic ones.
   ```python
   try:
       response = requests.get(url, timeout=timeout)
       response.raise_for_status()
   except requests.exceptions.ConnectionError:
       # Handle connection error
   except requests.exceptions.Timeout:
       # Handle timeout
   except requests.exceptions.HTTPError as e:
       if e.response.status_code == 429:
           # Handle rate limiting
       else:
           # Handle other HTTP errors
   ```

2. **Custom Exceptions**: Define custom exceptions for application-specific errors.
   ```python
   class ContentExtractionError(Exception):
       """Raised when content extraction fails."""
       pass
   
   def extract_content(html, selector):
       if not html or not selector:
           raise ContentExtractionError("HTML content or selector is empty")
       # Implementation
   ```

3. **Context Information**: Include context information in exceptions.
   ```python
   try:
       process_url(url)
   except Exception as e:
       raise RuntimeError(f"Error processing URL {url}") from e
   ```

### JavaScript/TypeScript Error Handling

1. **Async/Await with Try/Catch**: Use async/await with try/catch for asynchronous code.
   ```javascript
   async function fetchContent(url) {
       try {
           const response = await fetch(url);
           if (!response.ok) {
               throw new Error(`HTTP error: ${response.status}`);
           }
           return await response.text();
       } catch (error) {
           console.error(`Failed to fetch ${url}: ${error.message}`);
           throw error;
       }
   }
   ```

2. **Custom Error Classes**: Define custom error classes for application-specific errors.
   ```javascript
   class ContentExtractionError extends Error {
       constructor(message) {
           super(message);
           this.name = "ContentExtractionError";
       }
   }
   
   function extractContent(html, selector) {
       if (!html || !selector) {
           throw new ContentExtractionError("HTML content or selector is empty");
       }
       // Implementation
   }
   ```

## Logging

### Python Logging

1. **Logger Configuration**: Use the `logging` module with proper configuration.
   ```python
   import logging
   
   logger = logging.getLogger(__name__)
   
   def process_url(url):
       logger.info("Processing URL: %s", url)
       try:
           # Implementation
       except Exception as e:
           logger.exception("Error processing URL: %s", url)
           raise
   ```

2. **Log Levels**: Use appropriate log levels.
   - `DEBUG`: Detailed information for debugging
   - `INFO`: Confirmation that things are working as expected
   - `WARNING`: Indication that something unexpected happened
   - `ERROR`: Due to a more serious problem, the software has not been able to perform a function
   - `CRITICAL`: A serious error indicating that the program itself may be unable to continue running

3. **Structured Logging**: Use structured logging for complex data.
   ```python
   logger.info("Crawl completed", extra={
       "urls_processed": len(processed_urls),
       "successful": len(successful_urls),
       "failed": len(failed_urls),
       "duration_seconds": duration
   })
   ```

### JavaScript/TypeScript Logging

1. **Console Methods**: Use appropriate console methods.
   ```javascript
   console.debug("Detailed debug information");
   console.info("Processing URL:", url);
   console.warn("Rate limit approaching");
   console.error("Failed to process URL:", url, error);
   ```

2. **Custom Logger**: Consider implementing a custom logger for production.
   ```javascript
   class Logger {
       static debug(message, ...args) {
           if (process.env.NODE_ENV !== "production") {
               console.debug(`[DEBUG] ${message}`, ...args);
           }
       }
       
       static info(message, ...args) {
           console.info(`[INFO] ${message}`, ...args);
       }
       
       // Other methods
   }
   
   Logger.info("Processing URL:", url);
   ```

## Performance Considerations

### Python Performance

1. **Generator Functions**: Use generator functions for large datasets.
   ```python
   def process_urls(urls):
       for url in urls:
           yield process_url(url)
   ```

2. **Use Appropriate Data Structures**: Choose the right data structure for the task.
   ```python
   # Use sets for membership testing
   visited_urls = set()
   if url in visited_urls:
       return
   
   # Use dictionaries for key-value lookups
   url_content_map = {}
   content = url_content_map.get(url)
   ```

3. **Avoid N+1 Queries**: Batch database operations.
   ```python
   # Bad: N+1 queries
   for url in urls:
       db.insert_record(url, extract_content(url))
   
   # Good: Batch insert
   records = [(url, extract_content(url)) for url in urls]
   db.batch_insert(records)
   ```

### JavaScript/TypeScript Performance

1. **Array Methods**: Use appropriate array methods.
   ```javascript
   // Use map for transformations
   const normalizedUrls = urls.map(normalizeUrl);
   
   // Use filter for filtering
   const validUrls = urls.filter(isValidUrl);
   
   // Use find for finding a single element
   const mainUrl = urls.find(url => url.includes("index"));
   ```

2. **Memoization**: Use memoization for expensive operations.
   ```javascript
   const memoizedFetch = memoize(async (url) => {
       const response = await fetch(url);
       return response.text();
   });
   ```

3. **Debounce and Throttle**: Use debounce or throttle for frequent events.
   ```javascript
   const debouncedSearch = debounce((query) => {
       searchCrawlResults(query);
   }, 300);
   
   searchInput.addEventListener("input", (e) => {
       debouncedSearch(e.target.value);
   });
   ```

## Security Practices

### Input Validation

1. **URL Validation**: Validate URLs before processing.
   ```python
   def is_valid_url(url):
       pattern = re.compile(r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
       return bool(pattern.match(url))
   
   def process_url(url):
       if not is_valid_url(url):
           raise ValueError(f"Invalid URL: {url}")
       # Implementation
   ```

2. **Content Sanitization**: Sanitize content when necessary.
   ```python
   import html
   
   def sanitize_content(content):
       return html.escape(content)
   ```

### Data Protection

1. **Secure Storage**: Securely store sensitive data such as API keys.
   ```python
   # Use environment variables for sensitive information
   import os
   
   api_key = os.environ.get("API_KEY")
   if not api_key:
       raise EnvironmentError("API_KEY environment variable not set")
   ```

2. **Credential Handling**: Never hardcode credentials.
   ```python
   # Bad
   db_password = "my_secret_password"
   
   # Good
   db_password = os.environ.get("DB_PASSWORD")
   if not db_password:
       raise EnvironmentError("DB_PASSWORD environment variable not set")
   ```

### Web Security

1. **HTTPS Only**: Only crawl HTTPS URLs by default.
   ```python
   def validate_url(url):
       if not url.startswith("https://"):
           logger.warning("Non-HTTPS URL: %s", url)
           if not allow_http:
               raise ValueError(f"Non-HTTPS URL not allowed: {url}")
       # Additional validation
   ```

2. **Rate Limiting**: Implement rate limiting to respect website policies.
   ```python
   class RateLimiter:
       def __init__(self, requests_per_minute):
           self.rate = requests_per_minute
           self.interval = 60 / requests_per_minute
           self.last_request = 0
       
       def wait(self):
           current_time = time.time()
           elapsed = current_time - self.last_request
           if elapsed < self.interval:
               sleep_time = self.interval - elapsed
               time.sleep(sleep_time)
           self.last_request = time.time()
   ```

## Testing Standards

### Unit Tests

1. **Test File Organization**: Place test files in a `tests` directory with a structure mirroring the source.
   ```
   tests/
   ├── core/
   │   ├── test_crawler.py
   │   └── test_extractor.py
   ├── utils/
   │   ├── test_url_utils.py
   │   └── test_html_utils.py
   └── api/
       └── test_endpoints.py
   ```

2. **Naming Conventions**: Name test files with `test_` prefix and test methods with `test_` prefix.
   ```python
   # In test_crawler.py
   def test_crawl_single_url():
       # Test implementation
   
   def test_crawl_with_max_depth():
       # Test implementation
   ```

3. **Use Assertions**: Use appropriate assertions.
   ```python
   def test_extract_links():
       html = "<a href='https://example.com'>Link</a>"
       links = extract_links(html)
       assert len(links) == 1
       assert links[0] == "https://example.com"
   ```

### Integration Tests

1. **Test Real Components**: Test interactions between real components.
   ```python
   def test_crawler_with_extractor():
       crawler = Crawler()
       extractor = ContentExtractor()
       result = crawler.crawl("https://example.com", extractor=extractor)
       assert result.content is not None
       assert result.links is not None
   ```

2. **Mock External Services**: Use mocks for external services.
   ```python
   @patch("requests.get")
   def test_crawler_with_mock_http(mock_get):
       mock_response = MagicMock()
       mock_response.text = "<html><body>Test</body></html>"
       mock_response.status_code = 200
       mock_get.return_value = mock_response
       
       crawler = Crawler()
       result = crawler.crawl("https://example.com")
       assert "Test" in result.content
   ```

## Version Control Practices

1. **Branching Strategy**: Use a branching strategy like GitFlow.
   - `main`: Production-ready code
   - `develop`: Development code
   - `feature/*`: Feature branches
   - `bugfix/*`: Bug fix branches
   - `release/*`: Release preparation branches

2. **Commit Messages**: Write descriptive commit messages.
   ```
   feat: Add JavaScript rendering support for content extraction
   
   Add support for waiting until JavaScript loads before extracting content.
   This allows the crawler to extract content from single-page applications
   and other JavaScript-heavy sites.
   ```

3. **Pull Requests**: Create descriptive pull requests.
   - Title: Brief description of the changes
   - Description: Detailed description of the changes, the problem they solve, and any relevant issue numbers
   - Reviewers: Assign appropriate reviewers

## Conclusion

These coding standards aim to ensure code quality, maintainability, and security across the Crawl4AI project. All contributors are expected to follow these standards. 