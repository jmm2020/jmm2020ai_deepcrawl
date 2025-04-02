"""
Unit tests for the selectors module.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path to resolve imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.selectors import get_selectors_for_url, is_cli_documentation, GENERIC_SELECTORS, SUPABASE_CLI_SELECTORS


class TestSelectors(unittest.TestCase):
    """Tests for the selectors module."""
    
    def test_get_selectors_for_url_generic(self):
        """Test that generic URLs return generic selectors."""
        url = "https://example.com/docs/some-page"
        selectors = get_selectors_for_url(url)
        self.assertEqual(selectors, GENERIC_SELECTORS)
        
    def test_get_selectors_for_url_cli(self):
        """Test that CLI documentation URLs return specialized selectors."""
        url = "https://supabase.com/docs/reference/cli/supabase-inspect-db-locks"
        selectors = get_selectors_for_url(url)
        self.assertEqual(selectors, SUPABASE_CLI_SELECTORS)
        
    def test_is_cli_documentation_true(self):
        """Test that CLI documentation URLs are correctly identified."""
        cli_urls = [
            "https://supabase.com/docs/reference/cli/supabase-inspect-db-locks",
            "https://example.com/cli/some-command",
            "https://example.com/docs/cli/command",
            "https://example.com/cli-reference/command",
            "https://example.com/command-line/tool",
            "https://example.com/commands/run",
        ]
        
        for url in cli_urls:
            with self.subTest(url=url):
                self.assertTrue(is_cli_documentation(url))
                
    def test_is_cli_documentation_false(self):
        """Test that non-CLI documentation URLs are correctly identified."""
        non_cli_urls = [
            "https://example.com/docs/some-page",
            "https://example.com/api/endpoint",
            "https://example.com/reference/function",
            "https://example.com/guide/topic",
        ]
        
        for url in non_cli_urls:
            with self.subTest(url=url):
                self.assertFalse(is_cli_documentation(url))


if __name__ == "__main__":
    unittest.main() 