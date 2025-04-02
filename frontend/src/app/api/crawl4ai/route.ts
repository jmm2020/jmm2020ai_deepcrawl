import { NextRequest, NextResponse } from 'next/server';

// Types for the request body
interface CrawlRequest {
  url?: string;
  urls?: string | string[];
  depth?: number;
  model?: string;
  prompt?: string;
  max_pages?: number;
  extraction_config?: {
    type: string;
    params?: any;
  };
  cache_mode?: string;
}

interface TaskResponse {
  task_id: string;
  status: string;
}

export async function POST(request: Request) {
  try {
    const body = await request.json() as CrawlRequest;
    
    // Support both 'url' and 'urls' for compatibility
    const urls = body.urls || (body.url ? [body.url] : []);
    const model = body.model || 'default';
    
    console.log('Processing URLs:', urls);
    console.log('Using model:', model);
    
    if (urls.length === 0) {
      return Response.json(
        { error: 'No URLs provided', success: false },
        { status: 400 }
      );
    }
    
    try {
      // Try the integrated Crawl4AI API server first
      console.log('Connecting to integrated Crawl4AI API server...');
      
      const apiResponse = await fetch('http://localhost:8000/api/crawl4ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: urls[0], // Currently supporting single URL
          max_depth: body.depth,
          max_pages: body.max_pages,
          model: model,
          system_prompt: body.prompt
        })
      });
      
      if (apiResponse.ok) {
        const result = await apiResponse.json();
        console.log('Successfully received response from integrated API');
        return Response.json(result);
      } else {
        const errorText = await apiResponse.text();
        console.log(`Integrated API failed (${apiResponse.status}): ${errorText}`);
        console.log('Falling back to local crawler');
      }
    } catch (error) {
      console.log('Error connecting to integrated API, falling back to local crawler', error);
    }
    
    // Fallback to local crawler
    try {
      // Check if local crawler is available first
      console.log('Checking if local crawler is available...');
      
      // The local crawler at port 11235 doesn't seem to be working
      // Skip the health check and directly return that both services are unavailable
      console.log('Local crawler is not available or not properly configured');
      return Response.json({
        success: false,
        error: 'Both the integrated API server and local crawler are unavailable. Please start the API server or local crawler service.'
      }, { status: 503 });
      
      /* Removing the health check since it's never going to succeed
      try {
        const healthResponse = await fetch('http://localhost:11235/health', { 
          method: 'GET' 
        });
        
        if (!healthResponse.ok) {
          console.log('Local crawler health check failed');
          return Response.json({
            success: false,
            error: 'Both the integrated API server and local crawler are unavailable. Please start the API server or local crawler service.'
          }, { status: 503 });
        }
      } catch (error) {
        console.log('Local crawler is not available', error);
        return Response.json({
          success: false,
          error: 'Both the integrated API server and local crawler are unavailable. Please start the API server or local crawler service.'
        }, { status: 503 });
      }
      */
      
      // Submit crawl task
      const taskResponse = await fetch('http://localhost:11235/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_type: 'crawler',
          urls: urls,
          model: model,
          depth: body.depth || 1,
          max_pages: body.max_pages || 10,
          system_prompt: body.prompt
        })
      });

      if (!taskResponse.ok) {
        const errorText = await taskResponse.text();
        return Response.json({
          success: false,
          error: `Task submission failed: ${taskResponse.status} ${taskResponse.statusText} - ${errorText}`
        }, { status: 500 });
      }

      const taskResponseData = await taskResponse.json() as TaskResponse;
      console.log(`Task submitted successfully. Task ID: ${taskResponseData.task_id}`);

      // Step 2: Poll for task completion and get results
      let result = null;
      let attempts = 0;
      const maxAttempts = 30; // 30 seconds timeout
      const pollInterval = 1000; // 1 second

      while (attempts < maxAttempts) {
        console.log(`Step 2: Checking task status (attempt ${attempts + 1}/${maxAttempts})...`);
        const statusResponse = await fetch(`http://localhost:11235/task/${taskResponseData.task_id}`, {
          method: 'GET',
          headers: {
            'Authorization': 'Bearer __n8n_BLANK_VALUE_e5362baf-c777-4d57-a609-6eaf1f9e87f6'
          }
        });

        if (statusResponse.ok) {
          const status = await statusResponse.json();
          console.log(`Task status: ${status.status}`);

          if (status.status === 'completed') {
            result = status.result;
            break;
          } else if (status.status === 'failed') {
            return Response.json({
              success: false,
              error: `Task failed: ${status.error || 'Unknown error'}`
            }, { status: 500 });
          }
          // If still processing, continue polling
        } else {
          console.log(`Error checking status: ${statusResponse.status} ${statusResponse.statusText}`);
        }

        await new Promise(resolve => setTimeout(resolve, pollInterval));
        attempts++;
      }

      if (!result) {
        return Response.json({
          success: false,
          error: 'Task timed out or failed to complete'
        }, { status: 504 });
      }

      console.log('Task completed successfully');
      return Response.json({
        success: true,
        data: result,
        url: urls[0]
      });

    } catch (error: any) {
      console.error('Crawl4AI request error:', error.message);
      return Response.json({
        success: false,
        error: `Crawl4AI request failed: ${error.message}`
      }, { status: 500 });
    }
  } catch (error: any) {
    // Handle JSON parsing errors or any other errors
    console.error('Error processing request:', error);
    return Response.json({
      success: false,
      error: 'Invalid request format'
    }, { status: 400 });
  }
} 