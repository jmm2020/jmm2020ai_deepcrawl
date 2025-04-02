"""
Selectors for content extraction from different documentation types.

This module provides specialized selectors for extracting content from
various documentation formats, especially those that consistently fail
with generic extraction methods.

Usage:
    from utils.selectors import get_selectors_for_url
    selectors = get_selectors_for_url(url)
    # Use selectors in content extraction logic
"""

from typing import Dict, List, Optional
from urllib.parse import urlparse

# Generic documentation selectors that work for most sites
GENERIC_SELECTORS = [
    'article', 'main', '.content', '#content', '.post', '.article',
    '.documentation', '.docs-content', '.markdown-content', '.page-content',
    '[role="main"]', '.main-content', '#main-content'
]

# Supabase CLI documentation selectors
SUPABASE_CLI_SELECTORS = [
    '.docs-content',
    '.prose',
    'main article',
    '.content-container',
    '#docs-content-container'
]

# Structure for mapping domain patterns to specialized selectors
DOMAIN_SELECTOR_MAP = {
    'supabase.com': {
        'path_patterns': [
            '/docs/reference/cli/'
        ],
        'selectors': SUPABASE_CLI_SELECTORS
    }
}

def get_selectors_for_url(url: str) -> List[str]:
    """
    Get specialized selectors for a given URL based on domain and path patterns.
    
    Args:
        url: The URL to get selectors for
        
    Returns:
        List of CSS selectors to use for content extraction
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    path = parsed_url.path
    
    # Check if we have specialized selectors for this domain
    if domain in DOMAIN_SELECTOR_MAP:
        domain_config = DOMAIN_SELECTOR_MAP[domain]
        
        # Check if the path matches any patterns for this domain
        for pattern in domain_config.get('path_patterns', []):
            if pattern in path:
                # Return specialized selectors for this type of page
                return domain_config['selectors']
    
    # Return generic selectors if no specialized ones found
    return GENERIC_SELECTORS

def is_cli_documentation(url: str) -> bool:
    """
    Check if a URL is CLI documentation that might need specialized handling.
    
    Args:
        url: The URL to check
        
    Returns:
        True if the URL appears to be CLI documentation
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    path = parsed_url.path
    
    # Check for common CLI documentation patterns
    cli_patterns = [
        '/cli/',
        '/reference/cli/',
        '/docs/cli/',
        '/cli-reference/',
        '/command-line/',
        '/commands/'
    ]
    
    return any(pattern in path for pattern in cli_patterns) 