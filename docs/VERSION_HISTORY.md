# Version History

Last Updated: **April 2, 2024**

This document tracks version changes and major updates to the Crawl4AI project.

## Version 0.0.6 (Current)

**Date:** April 2, 2024

### New Features

- **Documentation Centralization**:
  - Created a comprehensive documentation structure in the `docs` directory
  - Added a central `INDEX.md` for navigating all documentation
  - Created detailed documentation for each major component and process
  - Standardized documentation format with last updated dates

- **JSON Post-Processing**:
  - Added robust tools for processing JSON files to Supabase
  - Implemented batch processing with configurable parameters
  - Added duplicate detection to prevent redundant database entries
  - Created retry mechanisms for handling transient failures
  - Added detailed logging for monitoring import processes

- **Improved Error Handling**:
  - Enhanced error handling in the crawling process
  - Implemented better retry mechanisms for content extraction
  - Added structured logging for error diagnosis
  - Created comprehensive troubleshooting guides

- **WebSocket Improvements**:
  - Removed unnecessary ping mechanism
  - Enhanced terminal output display with proper formatting
  - Improved connection management and resource cleanup
  - Fixed issues with real-time progress updates

- **Multi-URL Crawling Enhancements**:
  - Implemented rate limiting for concurrent requests
  - Added progress reporting for multi-URL crawls
  - Improved error handling for child link processing
  - Enhanced logging for multi-URL crawl operations

### Bug Fixes

- Fixed issues with WebSocket connection handling
- Resolved problems with content extraction on certain page types
- Addressed database connection and insertion failures
- Fixed process termination issues in server management scripts

### Documentation Updates

- Created comprehensive TESTING.md with detailed test procedures
- Added TROUBLESHOOTING.md for common issues and solutions
- Created JSON_PROCESSING.md guide for post-processing capabilities
- Developed CODE_STANDARDS.md and CONTRIBUTING.md for developers
- Added documentation section to main README with links to all guides

## Version 0.0.5

**Date:** March 25, 2024

### New Features

- **Multi-URL Crawling**:
  - Initial implementation of parallel crawling for multiple URLs
  - Added support for sitemap.xml parsing
  - Implemented concurrent request handling

- **WebSocket Communication**:
  - Added WebSocket support for real-time progress updates
  - Implemented terminal output capture and display

- **Database Integration**:
  - Initial Supabase integration for storing crawl results
  - Added embedded generation and storage

### Bug Fixes

- Fixed issues with content extraction on JavaScript-heavy pages
- Addressed memory leaks in long-running crawls
- Resolved race conditions in concurrent operations

## Version 0.0.4

**Date:** March 15, 2024

### New Features

- **Content Chunking**:
  - Implemented automatic content chunking for large pages
  - Added support for processing fragmented content

- **Enhanced Crawler Engine**:
  - Improved link extraction and normalization
  - Added depth control for crawling
  - Implemented domain restrictions for targeted crawling

### Bug Fixes

- Fixed issues with HTML parsing on malformed pages
- Addressed URL normalization problems
- Resolved path handling issues on different operating systems

## Version 0.0.3

**Date:** March 5, 2024

### New Features

- **Initial API Server**:
  - Implemented FastAPI-based server for crawler control
  - Added endpoints for starting and monitoring crawls
  - Created basic result retrieval functionality

- **Frontend Prototype**:
  - Developed initial web interface for crawler interaction
  - Added form for configuring crawl parameters
  - Implemented basic results display

### Bug Fixes

- Fixed issues with model loading and initialization
- Addressed configuration handling problems
- Resolved path reference issues in the project structure

## Version 0.0.2

**Date:** February 25, 2024

### New Features

- **Basic Crawler Engine**:
  - Implemented core crawler functionality
  - Added support for depth-limited crawling
  - Created content extraction capabilities
  - Added initial embedding generation

### Bug Fixes

- Fixed issues with HTTP request handling
- Addressed content parsing problems
- Resolved embedding generation errors

## Version 0.0.1

**Date:** February 15, 2024

### Initial Release

- **Core Structure**:
  - Created project structure and organization
  - Defined basic interfaces and components
  - Implemented fundamental crawling capabilities
  - Set up basic configuration handling 