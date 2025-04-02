# Testing Procedures

Last Updated: **April 2, 2024**

## Overview

This document provides testing procedures for the various components of the Crawl4AI system. It includes test plans, expected results, and validation steps for both component-level and system-level testing.

## Testing Categories

1. **Component Testing**: Testing individual components in isolation
2. **Integration Testing**: Testing interactions between components
3. **System Testing**: Testing the complete system end-to-end
4. **Performance Testing**: Testing system performance under various conditions
5. **Recovery Testing**: Testing system recovery from failures

## JSON Post-Processing Testing

### Initial Setup Testing

1. **Prerequisites**:
   - Supabase database is accessible
   - JSON file with crawl results is available
   - Required directories (`logs`, `results`) exist

2. **Script Execution Test**:
   ```bash
   cd workbench/scripts
   import_json_to_supabase.bat list
   ```
   
   **Expected Result**: List of available JSON files with timestamps and sizes

3. **Directory Structure Verification**:
   - Verify `logs` directory exists or is created
   - Verify script paths reference the correct directories
   - Verify permissions allow writing to log files

### Small-Scale Testing

1. **Basic Import Test**:
   ```bash
   import_json_to_supabase.bat results\[small_file].json
   ```
   
   **Expected Result**:
   - Terminal output shows successful insertion of records
   - Log file is created in the `logs` directory
   - Records are inserted into Supabase

2. **Custom Parameters Test**:
   ```bash
   import_json_to_supabase.bat results\[small_file].json 5 3 1.0
   ```
   
   **Expected Result**:
   - Terminal output shows processing in batches of 5
   - Records are successfully inserted into Supabase

### Duplicate Handling Testing

1. **Duplicate Detection Test**:
   - Run import command once to populate the database
   - Run the same import command again
   
   ```bash
   import_json_to_supabase.bat results\[same_file].json
   ```
   
   **Expected Result**:
   - Terminal output shows skipped duplicate records
   - Log file shows records were identified as duplicates
   - No duplicate records are inserted into Supabase

2. **Partial Duplicate Test**:
   - Create a JSON file with some records that already exist and some that don't
   - Run import command
   
   **Expected Result**:
   - Terminal output shows skipped duplicates and newly inserted records
   - Log file shows which records were skipped and which were inserted
   - Only new records are added to Supabase

### Large-Scale Testing

1. **Large File Test**:
   ```bash
   import_json_to_supabase.bat results\[large_file].json 20 5 2.0
   ```
   
   **Expected Result**:
   - Terminal output shows processing in batches of 20
   - Processing completes without memory or timeout issues
   - Records are successfully inserted into Supabase

2. **Performance Monitoring**:
   - Monitor system resource usage during import
   - Track insertion rate (records per minute)
   - Observe network and database response times
   
   **Expected Result**:
   - System remains responsive throughout the process
   - Resource usage remains within acceptable limits
   - Performance metrics are documented for future reference

### Error Recovery Testing

1. **Connection Interruption Test**:
   - Start an import process
   - Temporarily disconnect from the network or Supabase
   - Reconnect and observe retry behavior
   
   **Expected Result**:
   - Script attempts to retry failed operations
   - Terminal output shows retry attempts
   - Log file documents the failures and retries

2. **Process Interruption Test**:
   - Start an import process
   - Manually interrupt the process (Ctrl+C)
   - Restart the import process with the same file
   
   **Expected Result**:
   - Process detects previously inserted records as duplicates
   - New import continues without creating duplicates
   - Log file documents the continuation process

## WebSocket Communication Testing

1. **Connection Establishment Test**:
   - Start API server
   - Start frontend
   - Navigate to crawler page
   - Open browser developer tools and observe WebSocket connections
   
   **Expected Result**:
   - WebSocket connection is established
   - Connection confirmation message is received
   - No ping/pong messages are sent

2. **Terminal Output Capture Test**:
   - Start a crawl job
   - Observe terminal output in the progress window
   
   **Expected Result**:
   - Terminal output appears in real-time
   - Messages are prefixed with "[Terminal]"
   - All console output from the crawler is displayed

3. **Connection Closure Test**:
   - Start a small crawl job
   - Let it complete
   - Observe WebSocket behavior
   
   **Expected Result**:
   - WebSocket connection closes automatically
   - Closure message is received
   - No resources are leaked

## Database Integration Testing

1. **Database Connection Test**:
   - Start API server
   - Check database status endpoint
   
   **Expected Result**:
   - API returns database connection status
   - Error handling is appropriate for connection issues

2. **Record Insertion Test**:
   - Run a small crawl
   - Check database for inserted records
   
   **Expected Result**:
   - Records are inserted into Supabase
   - Embeddings are properly formatted
   - Metadata is preserved

## Reporting Test Results

When reporting test results, include:

1. **Test Environment**:
   - Hardware specifications
   - Software versions
   - Network configuration
   - Database configuration

2. **Test Execution**:
   - Steps performed
   - Commands executed
   - Parameters used
   - Timestamps

3. **Test Results**:
   - Success/failure counts
   - Error messages
   - Performance metrics
   - Screenshots or terminal output

4. **Analysis**:
   - Identified issues
   - Root causes
   - Recommendations for improvement
   - Follow-up actions

## Test Documentation Templates

### Test Case Template

```
Test Case ID: TC-XXX
Title: Brief description of the test
Priority: High/Medium/Low
Environment: Development/Staging/Production

Prerequisites:
- Required setup, data, or conditions

Steps:
1. First step
2. Second step
3. ...

Expected Results:
- What should happen after each step

Actual Results:
- What actually happened

Pass/Fail: Pass/Fail

Notes:
- Any additional observations or information
```

### Test Report Template

```
Test Report: [Feature/Component]
Test Date: YYYY-MM-DD
Tester: [Name]

Summary:
Brief overview of testing performed and results

Test Cases Executed:
- TC-001: Pass/Fail
- TC-002: Pass/Fail
- ...

Issues Found:
- Issue 1: Description
- Issue 2: Description
- ...

Recommendations:
- Recommendation 1
- Recommendation 2
- ...

Conclusion:
Overall assessment and next steps
``` 