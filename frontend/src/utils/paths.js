/**
 * Path utilities for the Crawl4AI project (JavaScript/Next.js version)
 * 
 * This module provides standardized path resolution functions to ensure
 * all components reference the same locations consistently.
 */

const path = require('path');
const fs = require('fs');

// Determine the Next.js root and workbench directory
const NEXTJS_ROOT = process.cwd();
const WORKBENCH_DIR = path.resolve(NEXTJS_ROOT, '..');

// Standard directory paths
const DIRS = {
  workbench: WORKBENCH_DIR,
  api: path.join(WORKBENCH_DIR, 'new_components'),
  frontend: NEXTJS_ROOT,
  docs: path.join(WORKBENCH_DIR, 'docs'),
  utils: path.join(WORKBENCH_DIR, 'utils'),
  data: path.join(WORKBENCH_DIR, 'data'),
};

/**
 * Get absolute path relative to a specific base directory
 * 
 * @param {string} relativePath - Path relative to the base directory
 * @param {string} base - Base directory key from DIRS (default is "frontend")
 * @returns {string} Absolute path
 * 
 * @example
 * // Get path to an API file
 * const apiPath = getPath('api_bridge.py', 'api');
 * 
 * @example
 * // Get path to a documentation file
 * const docsPath = getPath('PROGRESS.md', 'docs');
 */
function getPath(relativePath, base = 'frontend') {
  if (!DIRS[base]) {
    throw new Error(`Unknown base directory: ${base}. Valid options are: ${Object.keys(DIRS).join(', ')}`);
  }
  
  return path.join(DIRS[base], relativePath);
}

/**
 * Ensure a directory exists, creating it if necessary
 * 
 * @param {string} dirPath - Directory path to ensure exists
 * @returns {string} The directory path
 */
function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
  return dirPath;
}

// Export the utilities
module.exports = {
  DIRS,
  getPath,
  ensureDir,
  
  // Environment-specific constants
  ENV: {
    // API server URL with environment variable fallback
    API_SERVER: process.env.NEXT_PUBLIC_API_SERVER_URL || 'http://localhost:1111',
    // Ollama host with environment variable fallback
    OLLAMA_HOST: process.env.NEXT_PUBLIC_OLLAMA_HOST || 'http://localhost:11434',
  }
};

// If this file is executed directly, print debug info
if (require.main === module) {
  console.log('PROJECT STRUCTURE:');
  console.log('='.repeat(50));
  console.log(`Next.js Root: ${NEXTJS_ROOT}`);
  console.log(`Workbench Directory: ${WORKBENCH_DIR}`);
  
  for (const [name, dir] of Object.entries(DIRS)) {
    console.log(`${name.charAt(0).toUpperCase() + name.slice(1)} Directory: ${dir}`);
    console.log(`  ${fs.existsSync(dir) ? '✓ Directory exists' : '✗ Directory does not exist'}`);
  }
  
  console.log('\nEXAMPLES:');
  console.log('='.repeat(50));
  console.log(`API Bridge Path: ${getPath('api_bridge.py', 'api')}`);
  console.log(`Documentation Path: ${getPath('PROGRESS.md', 'docs')}`);
} 