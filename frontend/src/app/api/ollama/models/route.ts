import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  try {
    // Try calling our backend API server first
    const apiServer = process.env.NEXT_PUBLIC_API_SERVER_URL || 'http://localhost:1111';
    console.log(`Attempting to fetch models from API server: ${apiServer}/api/models`);
    
    try {
      const response = await fetch(`${apiServer}/api/models`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        // Add a timeout to prevent hanging
        signal: AbortSignal.timeout(5000)
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Successfully fetched models from API server:', data);
        return NextResponse.json(data);
      } else {
        console.log(`API server response not OK: ${response.status}`);
        // Continue to fallbacks
      }
    } catch (apiErr) {
      console.error('Error fetching from API server:', apiErr);
      // Continue to fallbacks
    }
    
    // Try communicating with Ollama directly as fallback
    console.log('Attempting to fetch models directly from Ollama');
    try {
      const ollamaHost = process.env.NEXT_PUBLIC_OLLAMA_HOST || 'http://localhost:11434';
      const ollamaResponse = await fetch(`${ollamaHost}/api/tags`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        // Add a timeout
        signal: AbortSignal.timeout(5000)
      });
      
      if (ollamaResponse.ok) {
        const ollamaData = await ollamaResponse.json();
        console.log('Successfully fetched models directly from Ollama:', ollamaData);
        
        // Transform Ollama response to match our API format
        if (ollamaData && Array.isArray(ollamaData.models)) {
          return NextResponse.json({
            success: true,
            completion_models: ollamaData.models.map((model: any) => ({
              name: model.name,
              size: model.size,
              modified_at: model.modified_at
            }))
          });
        }
      } else {
        console.log(`Ollama direct response not OK: ${ollamaResponse.status}`);
      }
    } catch (ollamaErr) {
      console.error('Error fetching directly from Ollama:', ollamaErr);
    }
    
    // Final fallback - provide a hardcoded list of common models
    console.log('Using hardcoded model list as fallback');
    return NextResponse.json({
      success: true,
      completion_models: [
        { name: "llama3:8b" },
        { name: "llama3:70b" },
        { name: "gemma3:27b" },
        { name: "gemma:7b" },
        { name: "mistral" },
        { name: "snowflake-arctic-embed2:latest" },
        { name: "neural-chat" },
        { name: "phi3" }
      ]
    });
  } catch (err) {
    const error = err instanceof Error ? err : new Error(String(err));
    console.error('Unhandled error in models API:', error);
    return NextResponse.json({
      success: false,
      error: error.message,
      completion_models: [
        { name: "llama3:8b" },
        { name: "gemma3:27b" },
        { name: "snowflake-arctic-embed2:latest" }
      ]  // Minimal fallback for UI
    }, { status: 500 });
  }
} 