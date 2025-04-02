# Troubleshooting Guide

Last Updated: **April 2, 2024**

## Overview

This guide provides solutions for common issues encountered when working with the Crawl4AI system. It includes troubleshooting steps for crawling problems, database connectivity issues, and general system errors.

## Crawling Issues

### Pages Not Being Crawled

**Symptoms**:
- URLs are provided but the crawler doesn't attempt to access them
- Crawler immediately reports completion without processing URLs

**Possible Causes**:
1. Invalid URL format
2. Network connectivity issues
3. Rate limiting configuration preventing requests

**Solutions**:
1. Verify URL format includes protocol (http:// or https://)
2. Check network connectivity with a simple ping or HTTP request
3. Review rate limiting settings in configuration file
4. Check crawler logs for specific error messages

### Content Extraction Failures

**Symptoms**:
- Crawler accesses pages but fails to extract content
- Empty or minimal content saved to database
- Error messages about selectors failing

**Possible Causes**:
1. Selector patterns don't match page structure
2. JavaScript-rendered content not being captured
3. Site structure has changed since selectors were defined
4. Anti-scraping measures blocking content access

**Solutions**:
1. Update selector patterns in `selectors.py` to match current page structure
2. Enable JavaScript rendering with the `--render-js` flag
3. Check for site structure changes and update selectors accordingly
4. Implement user-agent rotation or proxy usage for sensitive sites

### Rate Limiting and Blocking

**Symptoms**:
- HTTP 429 (Too Many Requests) errors
- Sudden failures after crawling several pages
- IP address being blocked

**Possible Causes**:
1. Crawler sending requests too quickly
2. Site has strict anti-bot measures
3. Concurrent requests exceeding site's limits

**Solutions**:
1. Increase delay between requests in configuration
2. Decrease number of concurrent requests
3. Implement exponential backoff for retry attempts
4. Use proxies to distribute requests across IPs
5. Add appropriate headers to mimic browser behavior

## Database Issues

### Connection Failures

**Symptoms**:
- Error messages about database connection failures
- Unable to start API server
- Insertion operations failing

**Possible Causes**:
1. Database credentials incorrect
2. Network issues preventing connection
3. Database service not running
4. Firewall blocking connections

**Solutions**:
1. Verify database credentials in `.env` file
2. Check network connectivity to database host
3. Ensure database service is running
4. Check firewall settings for database port
5. Verify VPN settings if connecting through VPN

### Data Insertion Failures

**Symptoms**:
- Crawler runs successfully but data isn't appearing in database
- Error messages about insertion failures
- Database constraint violations

**Possible Causes**:
1. Schema mismatch between code and database
2. Duplicate URL constraints being violated
3. Data format issues (e.g., null values where not allowed)
4. Database permissions issues

**Solutions**:
1. Verify schema matches between code models and database
2. Check for and handle duplicate URLs properly
3. Ensure all required fields have valid values
4. Verify database user has INSERT permissions
5. Use JSON post-processing for failed insertions (see `JSON_PROCESSING.md`)

### Embeddings Generation Issues

**Symptoms**:
- Records inserted without embeddings
- Error messages about embedding generation
- API calls failing with embedding-related errors

**Possible Causes**:
1. Embedding service not available
2. Text content too large for embedding service
3. API key or configuration issues

**Solutions**:
1. Verify embedding service is running
2. Check API key in configuration
3. Verify text chunking is working properly
4. Review logs for specific embedding service errors

## API Server Issues

### Server Won't Start

**Symptoms**:
- Error messages when starting API server
- Server starts but immediately crashes
- Port binding failures

**Possible Causes**:
1. Port already in use
2. Environment variables not set correctly
3. Dependencies missing
4. Python version incompatibility

**Solutions**:
1. Check if another process is using the configured port
2. Verify all required environment variables are set
3. Run `pip install -r requirements.txt` to install dependencies
4. Verify Python version (3.8+ recommended)

### WebSocket Connection Issues

**Symptoms**:
- Frontend not receiving real-time updates
- Error messages about WebSocket connection failures
- Terminal output not appearing in frontend

**Possible Causes**:
1. WebSocket server not running
2. Network/firewall blocking WebSocket connections
3. Frontend WebSocket client configuration issues

**Solutions**:
1. Verify WebSocket server is running alongside API server
2. Check browser console for WebSocket connection errors
3. Ensure frontend is configured with correct WebSocket URL
4. Disable any browser extensions that might interfere with WebSockets

## Frontend Issues

### UI Not Updating

**Symptoms**:
- Crawl progress not reflecting in UI
- Status indicators not changing
- Results not appearing after crawl completion

**Possible Causes**:
1. WebSocket connection issues
2. React state not updating properly
3. Event handling bugs

**Solutions**:
1. Check WebSocket connection in browser developer tools
2. Verify event handlers are properly registered
3. Check browser console for JavaScript errors
4. Reload the page and try again

### Form Submission Failures

**Symptoms**:
- Form submits but no action occurs
- Error messages when submitting forms
- Unexpected behavior after form submission

**Possible Causes**:
1. Form validation failures
2. API endpoint issues
3. CORS configuration problems

**Solutions**:
1. Check form validation rules
2. Verify API endpoints are correctly configured
3. Check for CORS errors in browser console
4. Verify form data structure matches API expectations

## System-Wide Issues

### Performance Problems

**Symptoms**:
- Slow crawling performance
- High CPU or memory usage
- System becoming unresponsive during operations

**Possible Causes**:
1. Too many concurrent operations
2. Memory leaks
3. Inefficient code patterns
4. Hardware limitations

**Solutions**:
1. Decrease concurrent operations
2. Monitor memory usage and identify leaks
3. Optimize code for performance-critical paths
4. Upgrade hardware if necessary

### Log Analysis

When troubleshooting issues, check the following log files:

1. **Crawler Logs**: Located in `logs/crawler_*.log`
   - Check for HTTP errors, parsing failures, and rate limiting issues

2. **API Server Logs**: Located in `logs/api_*.log`
   - Check for connection issues, endpoint failures, and database errors

3. **JSON Processing Logs**: Located in `logs/json_import_*.log`
   - Check for insertion failures, duplicate records, and Supabase API issues

4. **Frontend Console**: Accessible via browser developer tools
   - Check for JavaScript errors, WebSocket issues, and React rendering problems

## Getting Additional Help

If you've followed the troubleshooting steps above and are still experiencing issues:

1. **Check Issue Tracker**: Review existing issues on the project repository
2. **Gather Information**:
   - Exact error messages
   - Steps to reproduce the issue
   - Log files and screenshots
   - System information (OS, Python version, etc.)
3. **Create Detailed Report**: Include all gathered information when reporting the issue

## Common Error Messages and Solutions

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| `ConnectionError: Max retries exceeded` | Network issues or target site down | Check network, increase retry count |
| `selector.py line X: No elements matched` | Selector pattern doesn't match page | Update selector patterns |
| `psycopg2.OperationalError: could not connect to server` | Database connection issue | Check database credentials and connectivity |
| `TypeError: Object of type X is not JSON serializable` | Data structure contains non-JSON types | Fix data serialization in code |
| `WebSocket connection failed` | WebSocket server not running or network issue | Start WebSocket server, check network |
| `Cannot read property 'X' of undefined` | Frontend JavaScript error | Check React component props and state | 