# Next Steps

Last Updated: **April 2, 2024**

This document outlines the planned next steps for the Crawl4AI project, organized by priority and category.

## High Priority Tasks

### Path and Import Fixes

1. **Fix API Bridge Import Error**:
   - In `workbench/core/integrated_workflow.py`, update the import statement:
     ```python
     # Change from:
     from db_adapter import SupabaseAdapter
     
     # To:
     from core.db_adapter import SupabaseAdapter
     ```
   - Verify that all import paths are relative to their location within the project structure
   - Test API startup with `cd workbench && python api/api_bridge.py`

2. **Update Script Paths**:
   - Review and update all startup scripts to use correct paths 
   - Ensure all batch files (`start-all.bat`, etc.) reference correct file locations
   - Add directory change commands where necessary

### Content Extraction Improvements

1. **Fix CLI Documentation Crawling**:
   - Analyze patterns in failed crawls of CLI documentation pages (e.g., `https://supabase.com/docs/reference/cli/...`)
   - Identify common structure and create specialized selectors for CLI documentation
   - Update `selectors.py` with new patterns specific to CLI documentation pages

2. **Implement Additional Retry Strategies**:
   - Develop specialized fallback methods for different page types
   - Add delay variation to retry attempts to handle rate-limiting more effectively
   - Implement content extraction logging to identify patterns in failures

### GitHub Setup

1. **Initialize GitHub Repository**:
   - ✅ Create a new GitHub repository for the project
   - ✅ Set up appropriate .gitignore file for Python/Node.js projects
   - ✅ Add necessary GitHub configuration files

2. **Initial Repository Structure**:
   - ✅ Organize the initial commit with all core files
   - ✅ Include comprehensive documentation
   - ✅ Set up branch protection rules for main branch

3. **Workflow and Issue Templates**:
   - ✅ Create GitHub Actions workflow for basic validation
   - ✅ Set up issue templates for bug reports and feature requests
   - ✅ Add pull request template with checklist for contributors

4. **Documentation for GitHub Workflow**:
   - ✅ Update CONTRIBUTING.md with GitHub-specific processes
   - ✅ Document branching strategy and contribution workflow
   - ✅ Add instructions for creating issues and pull requests

5. **GitHub Repository Management**:
   - Create initial release and version tag
   - Configure branch protection for main and dev branches
   - Set up project boards for task management
   - Add README badges for build status and code coverage

## Medium Priority Tasks

### Database Integration

1. **Improve Supabase Connection Reliability**:
   - Implement connection pooling for better resource management
   - Add circuit breaker pattern to prevent cascade failures
   - Create comprehensive error logging for database operations

2. **Extend Post-Processing Capabilities**:
   - Add support for incremental updates to existing database records
   - Implement content diff functionality to update changed content
   - Create database cleanup utilities for removing stale or duplicate data

### Testing Framework

1. **Develop Automated Test Suite**:
   - Create pytest fixtures for common test scenarios
   - Implement integration tests for crawling, processing, and storage workflow
   - Add performance benchmarking for different crawl configurations

2. **Set Up Continuous Testing**:
   - Create automated test execution scripts
   - Implement scheduled test runs for regression detection
   - Develop test reporting and visualization dashboard

## Long-Term Goals

### Architecture Improvements

1. **API Enhancements**:
   - Implement OpenAPI documentation generation
   - Add middleware for authentication and rate limiting
   - Create comprehensive API error handling framework

2. **Crawler Architecture**:
   - Evaluate moving to a distributed crawler architecture
   - Research domain-specific crawling optimizations
   - Investigate queue-based work distribution for improved scalability

### User Experience Enhancements

1. **Frontend Improvements**:
   - Add visualization of crawl progress and results
   - Implement advanced configuration options in UI
   - Develop dashboard for analyzing crawl performance and success rates

2. **Documentation Experience**:
   - Add interactive examples to documentation
   - Create video tutorials for common workflows
   - Implement versioned documentation for different releases

## Issues Discovered During Work

### Import and Path Issues

- ✅ API bridge fails to load due to incorrect import paths
- ✅ Terminal command `cd workbench && python api/api_bridge.py` fails with:
  ```
  ModuleNotFoundError: No module named 'db_adapter'
  ```
- ✅ Need to update relative imports in core modules

### Content Extraction Failures

- ✅ Pattern of failures on CLI documentation pages:
  ```
  Progress log: Processing page: https://supabase.com/docs/reference/cli/supabase-inspect-db-locks
  Progress log: ✗ Failed to process: https://supabase.com/docs/reference/cli/supabase-inspect-db-locks
  ```
- ✅ Need specialized selectors for CLI documentation format
- ✅ All CLI documentation pages show systematic extraction failures

### Frontend Configuration

- Frontend successfully runs on port 3112:
  ```
  > next dev -p 3112
  - Local:        http://localhost:3112
  - Network:      http://192.168.0.148:3112
  ```
- API server needs to be started and properly configured

## Action Items for Next Session

1. ✅ Fix core module import paths to resolve API bridge startup failures
2. ✅ Update scripts to use correct paths and working directory
3. ✅ Analyze CLI documentation page structure to improve content extraction
4. ✅ Create specialized selector patterns for different documentation formats
5. Test the full workflow with both API and frontend after path fixes
6. Set up GitHub repository with initial project structure and documentation

## Additional Tasks Discovered

1. **Expand Selector Support**:
   - Add specialized selectors for more documentation formats (like API reference pages)
   - Create selectors for other platforms with extraction issues
   - Implement auto-detection of page types beyond just CLI documentation
   
2. **Improve Test Coverage**:
   - Add unit tests for content extraction functionality
   - Create tests with sample HTML from problematic pages
   - Implement integration tests for the full crawling workflow
   
3. **Content Post-Processing**:
   - Add markdown cleanup functionality for better formatting
   - Implement HTML-to-markdown conversion improvements
   - Add table extraction support for CLI command option tables
   
4. **Frontend Integration**:
   - Test and verify that content extraction improvements are visible in frontend
   - Update frontend to show page type detection
   - Add debugging info to help diagnose future extraction issues 