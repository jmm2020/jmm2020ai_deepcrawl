"""
Path utilities for the Crawl4AI project.

This module provides standardized path resolution functions to ensure
all components reference the same locations consistently.
"""

import os
import sys
from pathlib import Path
from typing import Union, Optional

# Determine the project root (parent of the workbench directory)
WORKBENCH_DIR = Path(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
PROJECT_ROOT = WORKBENCH_DIR.parent

# Define standard directories
DIRS = {
    "workbench": WORKBENCH_DIR,
    "api": WORKBENCH_DIR / "new_components",
    "frontend": WORKBENCH_DIR / "web_frontend",
    "docs": WORKBENCH_DIR / "docs",
    "utils": WORKBENCH_DIR / "utils",
    "data": WORKBENCH_DIR / "data",
}

def get_path(relative_path: str, base: Optional[str] = "workbench") -> Path:
    """
    Get absolute path relative to a specific base directory.
    
    Args:
        relative_path: Path relative to the base directory
        base: Base directory key from DIRS (default is "workbench")
    
    Returns:
        Absolute path as a Path object
    
    Examples:
        >>> get_path("docs/PROGRESS.md")
        PosixPath('/path/to/workbench/docs/PROGRESS.md')
        
        >>> get_path("api_bridge.py", base="api")
        PosixPath('/path/to/workbench/new_components/api_bridge.py')
    """
    if base not in DIRS:
        raise ValueError(f"Unknown base directory: {base}. Valid options are: {', '.join(DIRS.keys())}")
    
    return DIRS[base] / relative_path

def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
        
    Returns:
        Path object to the directory
    """
    path_obj = Path(path) if isinstance(path, str) else path
    os.makedirs(path_obj, exist_ok=True)
    return path_obj

def add_to_python_path():
    """Add the project root to the Python path if not already there."""
    project_root_str = str(PROJECT_ROOT)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)

# Add project root to Python path when this module is imported
add_to_python_path()

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def get_results_path(filename: Optional[str] = None) -> Union[Path, str]:
    """
    Get the path to the results directory or a specific file in it.
    
    Args:
        filename: Optional name of the file to include in the path
        
    Returns:
        Path to the results directory or specified file
    """
    results_dir = get_project_root() / "results"
    results_dir.mkdir(exist_ok=True)
    
    if filename:
        return str(results_dir / filename)
    return results_dir

def get_api_path() -> Path:
    """Get the path to the API directory."""
    return get_project_root() / "api"

def get_core_path() -> Path:
    """Get the path to the core directory."""
    return get_project_root() / "core"

if __name__ == "__main__":
    # Print the directory structure if run directly
    print(f"PROJECT STRUCTURE:\n{'=' * 50}")
    print(f"Project Root: {PROJECT_ROOT}")
    
    for name, path in DIRS.items():
        print(f"{name.capitalize()} Directory: {path}")
        if path.exists():
            print(f"  ✓ Directory exists")
        else:
            print(f"  ✗ Directory does not exist")
    
    # Examples of usage
    print(f"\nEXAMPLES:\n{'=' * 50}")
    print(f"API Bridge Path: {get_path('api_bridge.py', base='api')}")
    print(f"Documentation Path: {get_path('PROGRESS.md', base='docs')}") 