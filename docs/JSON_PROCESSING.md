# JSON Post-Processing Guide

Last Updated: **April 2, 2024**

## Overview

This document explains how to use the JSON post-processing tools to import crawl result files into Supabase when the initial database insertion during crawling fails.

## JSON Post-Processing Tools

We have implemented a set of tools to handle JSON files that failed to be inserted into Supabase during the initial crawl:

- `process_json_to_supabase.py`: Python script for processing JSON files and inserting them into Supabase
- `import_json_to_supabase.bat`: Windows batch script for easy execution of the Python script
- `list_crawl_results.bat`: Script to list all available crawl result files

## When to Use JSON Post-Processing

Use these tools when:

1. The crawler successfully generated JSON files but failed to insert data into Supabase
2. You want to recover data from previously crawled sites
3. You need to populate the Supabase database with crawl results from another source

## Using the Tools

### Listing Available Files

To see all available crawl result JSON files:

```bash
cd workbench/scripts
import_json_to_supabase.bat list
```

This will display a formatted list of all JSON files in the results directory, including:
- File ID
- Creation date and time
- File size
- Filename

### Basic Import

To import a specific JSON file:

```bash
import_json_to_supabase.bat results\crawl_results_20250402_123456.json
```

This will:
1. Check for existing records in Supabase to avoid duplicates
2. Process the JSON file in batches (default: 10 records per batch)
3. Retry failed insertions (default: 3 attempts)
4. Log successes, failures, and skipped duplicates
5. Generate a detailed log file in the `logs` directory

### Advanced Import Options

You can customize the import process with additional parameters:

```bash
import_json_to_supabase.bat path\to\file.json [batch_size] [retry_count] [delay]
```

Parameters:
- `batch_size`: Number of records to process in each batch (default: 10)
- `retry_count`: Number of retries for failed insertions (default: 3)
- `delay`: Delay in seconds between batches (default: 1.0)

Example with custom parameters:
```bash
import_json_to_supabase.bat results\crawl_results_20250402_123456.json 20 5 2
```

This will process 20 records at a time, retry failures up to 5 times, and wait 2 seconds between batches.

## Duplicate Handling

The tools automatically check for duplicate records to maintain data integrity:

1. Before processing, the script queries Supabase for all existing URLs
2. URLs that already exist in the database are skipped and marked as duplicates
3. A running count of skipped duplicates is maintained and reported

## Log Files

Each import process generates a detailed log file in the `logs` directory with the format:
```
supabase_import_YYYYMMDD_HHMMSS.log
```

These log files contain:
- Total number of records processed
- Successfully inserted records
- Failed insertion attempts with error messages
- Skipped duplicates
- Batch-by-batch progress
- Overall success rate

## Recommended Parameters

Based on our testing, we recommend the following parameters for different scenarios:

| Scenario | Batch Size | Retry Count | Delay | Example |
|----------|------------|-------------|-------|---------|
| Small files (<50 pages) | 5-10 | 3 | 1.0 | `import_json_to_supabase.bat file.json 5 3 1.0` |
| Medium files (50-500 pages) | 10-20 | 3 | 1.5 | `import_json_to_supabase.bat file.json 15 3 1.5` |
| Large files (>500 pages) | 20-30 | 5 | 2.0 | `import_json_to_supabase.bat file.json 25 5 2.0` |

## Troubleshooting

### Common Issues

1. **Connection Errors**:
   - Verify Supabase is running and accessible
   - Check network connectivity
   - Ensure your Supabase URL and key are correct

2. **Insertion Failures**:
   - Check log files for specific error messages
   - Increase retry count for intermittent issues
   - Verify JSON file structure and content

3. **Performance Issues**:
   - Decrease batch size if experiencing timeouts
   - Increase delay between batches if rate-limited
   - Monitor system resources during import

### Log File Analysis

When analyzing log files, look for patterns in failures:
- Do failures occur with specific URL patterns?
- Are there consistent error messages?
- Do failures happen at specific points in the process?

## Testing

See [TESTING.md](./TESTING.md) for detailed information on testing the JSON post-processing tools. 