"""
Crawl4AI Project Utilities Package

This package contains utility modules for the Crawl4AI project.
"""

from pathlib import Path

# Export the path utilities 
try:
    from .paths import get_path, ensure_dir, DIRS
except ImportError:
    # Handle the case where this is imported before paths.py exists
    def get_path(*args, **kwargs):
        raise NotImplementedError("paths.py module not available")

    def ensure_dir(path):
        raise NotImplementedError("paths.py module not available")
    
    DIRS = {} 