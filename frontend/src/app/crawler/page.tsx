'use client';

import Navbar from '@/components/Navbar';
import { useState, useEffect, useRef } from 'react';
import { ArrowRight, Database, Link, Search, Settings, Send } from 'lucide-react';
import SpaceTravelEffect from '@/components/SpaceTravelEffect';

export default function CrawlerPage() {
  const [url, setUrl] = useState('');
  const [maxDepth, setMaxDepth] = useState(2);
  const [maxPages, setMaxPages] = useState(50);
  const [model, setModel] = useState('llama2');
  const [embeddingModel, setEmbeddingModel] = useState('snowflake-arctic-embed2');
  const [promptType, setPromptType] = useState('standard');
  const [useSitemap, setUseSitemap] = useState(false);
  const [skipPageLimit, setSkipPageLimit] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState(
    `WEB CONTENT EXTRACTION AND PROCESSING

PRIMARY OBJECTIVE:
Extract high-quality, structured information from webpages to create a comprehensive knowledge base for retrieval augmented generation (RAG) systems.

EXTRACTION GUIDELINES:
1. METADATA EXTRACTION
   - Page title: Extract the complete, accurate title as displayed in browser tabs
   - Publication date: Identify and standardize to ISO format (YYYY-MM-DD)
   - Author information: Extract name(s) and credentials when available
   - URL: Preserve the canonical URL

2. CONTENT EXTRACTION
   - Main content: Isolate primary textual content from navigation, ads, and sidebars
   - Preserve semantic structure: Maintain heading hierarchy (H1, H2, H3, etc.)
   - Extract meaningful lists, tables, and structured data with formatting preserved
   - Remove duplicate content, navigation elements, and promotional material

3. SEMANTIC ANALYSIS
   - Identify 3-7 primary topics covered in the content
   - Extract key entities (people, organizations, products, locations)
   - Generate 3-5 relevant keywords for content categorization
   - Summarize the main content in 2-3 concise paragraphs

4. LINK PROCESSING
   - Validate all extracted links with HTTP status code checking
   - Only include links returning 200 status codes
   - Categorize links as: internal navigation, external references, citation sources
   - Prioritize links to authoritative sources or supporting documentation

5. CONTENT VERIFICATION
   - Flag potential misinformation or factually questionable content
   - Note content currency/freshness based on publication date
   - Document access limitations (paywalls, login requirements)

6. OUTPUT FORMATTING
   - Structure all extracted data in consistent JSON format
   - Ensure UTF-8 encoding for all text content
   - Preserve important formatting (bold, italics, lists) using markdown
   - Include metadata about extraction process (timestamp, version)

PROCESSING CONSTRAINTS:
- Process each page as standalone content while preserving context
- Document any extraction failures or limitations encountered

ERROR HANDLING:
- Gracefully handle malformed HTML, JavaScript-dependent content
- Record partial extractions when complete processing fails
- Provide detailed error logs for debugging and system improvement`
  );
  const [customPrompt, setCustomPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'configure' | 'crawl' | 'results' | 'chat'>('configure');
  const [chatMessages, setChatMessages] = useState<{role: string, content: string}[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [progressLogs, setProgressLogs] = useState<string[]>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const [availableModels, setAvailableModels] = useState<{name: string}[]>([{name: 'llama2'}]);
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [currentStatus, setCurrentStatus] = useState<string>('');
  const [elapsedTime, setElapsedTime] = useState(0);
  const startTimeRef = useRef(0);

  // State to track previously seen logs to avoid duplicates
  const [processedLogKeys, setProcessedLogKeys] = useState<Record<string, boolean>>({});
  
  // Function to safely merge logs, preserving order and avoiding duplicates
  const mergeLogs = (existingLogs: string[], newLogs: string[]): string[] => {
    if (!newLogs || newLogs.length === 0) return existingLogs;
    
    // Create a copy of existing logs
    const result = [...existingLogs];
    
    // Add all new logs with minimal deduplication
    for (const log of newLogs) {
      // Skip empty logs
      if (!log.trim()) continue;
      
      // Almost all logs should be displayed - only deduplicate if exactly the same message appears
      // multiple times in a short sequence (likely a UI error)
      
      // Common log patterns that should always be shown (even duplicates)
      const isProgressLog = log.includes("Processing") || 
                           log.includes("Generated") || 
                           log.includes("Successfully") || 
                           log.includes("Completed") || 
                           log.includes("Embedding") ||
                           log.includes("Content stats") ||
                           log.includes("Title:") ||
                           /\d+/.test(log);  // Contains any numbers
      
      // Always add logs that contain common progress patterns or numbers
      if (isProgressLog) {
        result.push(log);
        continue;
      }
      
      // For other logs, only deduplicate if the exact same message appears 
      // in the last 3 entries (to avoid rapid repeats)
      const lastThreeLogs = result.slice(-3);
      if (!lastThreeLogs.includes(log)) {
        result.push(log);
      }
    }
    
    return result;
  };

  // Fetch available models on component mount
  useEffect(() => {
    const fetchModels = async () => {
      setIsLoadingModels(true);
      try {
        const response = await fetch('/api/ollama/models');
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.completion_models && data.completion_models.length > 0) {
            setAvailableModels(data.completion_models);
            console.log('Available models:', data.completion_models);
          }
        }
      } catch (err) {
        console.error('Error fetching models:', err);
      } finally {
        setIsLoadingModels(false);
      }
    };
    
    fetchModels();
  }, []);

  // Auto-scroll logs to bottom when they update
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [progressLogs]);

  // Effect for timer when loading
  useEffect(() => {
    let timer: NodeJS.Timeout;
    
    if (isLoading) {
      // Reset and start the timer
      startTimeRef.current = Date.now();
      setElapsedTime(0);
      
      timer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
        setElapsedTime(elapsed);
      }, 1000);
    }
    
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isLoading]);
  
  // Format elapsed time as MM:SS
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  // Function to connect WebSocket
  const connectWebSocket = (jobId: string) => {
    const API_URL = process.env.NEXT_PUBLIC_API_SERVER_URL || 'http://localhost:1111';
    const wsUrl = API_URL.replace('http', 'ws');
    const ws = new WebSocket(`${wsUrl}/ws/${jobId}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      // Send a single ping message to request initial status, then stop pinging
      ws.send('ping');
    };

    ws.onmessage = (event) => {
      try {
        console.log('WebSocket raw message:', event.data);
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);

        if (data.type === 'progress') {
          if (data.message) {
            setProgressLogs(prevLogs => mergeLogs(prevLogs, [data.message]));
            console.log('Added progress log:', data.message);
          }
          if (data.status) {
            setCurrentStatus(data.status);
            // If job is complete, stop loading state
            if (data.status === 'completed' || data.status === 'error' || data.status === 'failed') {
              setIsLoading(false);
            }
          }
        } else if (data.type === 'status') {
          setCurrentStatus(data.status || 'processing');
          
          // If job is complete, stop loading state and fetch results
          if (data.status === 'completed' || data.status === 'error' || data.status === 'failed') {
            setIsLoading(false);
            
            // Display any message from server
            if (data.message) {
              setProgressLogs(prevLogs => mergeLogs(prevLogs, [data.message]));
            }
            
            // Only fetch results if completed successfully
            if (data.status === 'completed') {
              fetchResults(jobId);
            }
          }
        }
      } catch (error) {
        console.error('Error handling WebSocket message:', error, 'Raw data:', event.data);
      }
    };

    ws.onclose = (event) => {
      console.log('WebSocket disconnected', event.code, event.reason);
      setIsConnected(false);
      
      // If we get a normal closure with a reason, add it to logs
      if (event.code === 1000 && event.reason) {
        setProgressLogs(prevLogs => mergeLogs(prevLogs, [`WebSocket: ${event.reason}`]));
      }
      
      // If loading was still true, turn it off
      setIsLoading(false);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket connection error');
      setIsLoading(false);
    };

    setSocket(ws);

    return ws;
  };

  // Function to fetch final results
  const fetchResults = async (jobId: string) => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_SERVER_URL || 'http://localhost:1111';
      const response = await fetch(`${API_URL}/api/results/${jobId}`);
      
      if (!response.ok) {
        throw new Error(`Results API error (${response.status})`);
      }
      
      const resultsData = await response.json();
      if (resultsData.results && Array.isArray(resultsData.results)) {
        setResults(resultsData);
        setProgressLogs(prevLogs => [...prevLogs, `✓ Retrieved ${resultsData.results.length} crawled pages`]);
        setActiveTab('results');
      }
    } catch (error) {
      console.error('Error fetching results:', error);
      setError(error instanceof Error ? error.message : 'Failed to fetch results');
    }
  };

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [socket]);

  const handleCrawl = async () => {
    if (!url) return;
    
    setIsLoading(true);
    setResults(null);
    setProgressLogs([]);
    setProcessedLogKeys({}); // Reset processed log keys
    setError(null);
    setCurrentStatus('Starting crawler...');
    
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_SERVER_URL || 'http://localhost:1111';
      console.log(`Submitting crawl request to ${API_URL}/api/crawl with:`, {
        url,
        max_depth: maxDepth,
        max_pages: skipPageLimit ? 0 : maxPages,
        model: model,
        embedding_model: embeddingModel,
        use_sitemap: useSitemap
      });
      
      const response = await fetch(`${API_URL}/api/crawl`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          max_depth: maxDepth,
          max_pages: skipPageLimit ? 0 : maxPages,
          model: model,
          embedding_model: embeddingModel,
          system_prompt: systemPrompt,
          use_sitemap: useSitemap
        })
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`API error (${response.status}): ${errorText}`);
        throw new Error(`API error (${response.status}): ${errorText}`);
      }
      
      const responseData = await response.json();
      console.log('Crawl request response:', responseData);
      const { job_id } = responseData;
      setProgressLogs(logs => [...logs, `Job started with ID: ${job_id}`]);
      
      // Connect WebSocket for real-time updates
      connectWebSocket(job_id);
      
    } catch (error) {
      console.error('Crawl error:', error);
      setError(error instanceof Error ? error.message : 'Failed to crawl the URL');
      setResults({ 
        error: error instanceof Error ? error.message : 'Failed to crawl the URL',
        status: 'error',
        pages: []
      });
      setIsLoading(false);
    }
  };

  const handleChat = () => {
    if (!chatInput.trim()) return;
    
    const newMessage = { role: 'user', content: chatInput };
    const updatedMessages = [...chatMessages, newMessage];
    setChatMessages(updatedMessages);
    setChatInput('');
    
    // In a production app, this would call an API endpoint to query the vector database
    setTimeout(() => {
      setChatMessages([
        ...updatedMessages, 
        { 
          role: 'assistant', 
          content: `This is a simulated response based on the knowledge from "${url}". In a real implementation, this would query your vector database with your crawled data.` 
        }
      ]);
    }, 1000);
  };

  return (
    <main className="min-h-screen h-full relative overflow-auto bg-gray-900">
      <SpaceTravelEffect />
      <Navbar />
      <div className="flex flex-col pt-16 pb-10">
        <div className="container mx-auto p-4">
          <h1 className="text-2xl font-bold mb-6">Web Crawler with Ollama LLM</h1>
          
          {/* Performance Note - replaced warning */}
          <div className="p-4 mb-4 border border-blue-500/30 rounded-lg bg-blue-900/20">
            <h3 className="font-medium text-blue-300 mb-2">Performance Information</h3>
            <p className="text-gray-300 mb-2">This crawler is configured to use high-performance settings for your hardware.</p>
            <ul className="list-disc pl-5 text-sm text-gray-300">
              <li className="mb-1">Using <b>{embeddingModel}</b> for embeddings (proven to work with 90+ pages)</li>
              <li className="mb-1">Default depth of <b>{maxDepth}</b> and max pages of <b>{maxPages}</b> (can be adjusted)</li>
              <li className="mb-1">For extremely large sites, consider using domain filtering</li>
            </ul>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-4">
            <div 
              onClick={() => setActiveTab('configure')}
              className={`
                flex items-center justify-center p-4 rounded-lg border cursor-pointer transition-all duration-200 backdrop-blur-md
                ${activeTab === 'configure' ? 'border-cyan-500 bg-cyan-500/10' : 'border-white/20 hover:border-cyan-500/50 bg-black/20'}
              `}
            >
              <Settings className="mr-2" size={18} />
              <span>Configure</span>
            </div>
            <div 
              onClick={() => setActiveTab('crawl')}
              className={`
                flex items-center justify-center p-4 rounded-lg border cursor-pointer transition-all duration-200 backdrop-blur-md
                ${activeTab === 'crawl' ? 'border-cyan-500 bg-cyan-500/10' : 'border-white/20 hover:border-cyan-500/50 bg-black/20'}
              `}
            >
              <Search className="mr-2" size={18} />
              <span>Crawl</span>
            </div>
            <div 
              onClick={() => setActiveTab('results')}
              className={`
                flex items-center justify-center p-4 rounded-lg border cursor-pointer transition-all duration-200 backdrop-blur-md
                ${activeTab === 'results' ? 'border-cyan-500 bg-cyan-500/10' : 'border-white/20 hover:border-cyan-500/50 bg-black/20'}
              `}
            >
              <Database className="mr-2" size={18} />
              <span>Results</span>
            </div>
            <div 
              onClick={() => setActiveTab('chat')}
              className={`
                flex items-center justify-center p-4 rounded-lg border cursor-pointer transition-all duration-200 backdrop-blur-md
                ${activeTab === 'chat' ? 'border-cyan-500 bg-cyan-500/10' : 'border-white/20 hover:border-cyan-500/50 bg-black/20'}
              `}
            >
              <Link className="mr-2" size={18} />
              <span>Chat</span>
            </div>
          </div>
          
          <div className="border border-white/20 rounded-lg p-6 backdrop-blur-md bg-black/30">
            {activeTab === 'configure' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold mb-4">Crawler Configuration</h2>
                
                <div>
                  <label className="block text-sm font-medium mb-2">URL to Crawl</label>
                  <input
                    type="text"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://example.com"
                    className="w-full p-3 rounded-lg bg-black/40 border border-white/20 focus:border-cyan-500 outline-none"
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium mb-2">Crawl Depth</label>
                    <select
                      value={maxDepth}
                      onChange={(e) => setMaxDepth(Number(e.target.value))}
                      className="w-full p-3 rounded-lg bg-black/40 border border-white/20 focus:border-cyan-500 outline-none"
                    >
                      {[1, 2, 3, 4, 5].map(d => (
                        <option key={d} value={d}>{d}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-2">Max Pages</label>
                    <input
                      type="number"
                      value={maxPages}
                      onChange={(e) => setMaxPages(Number(e.target.value))}
                      min="1"
                      className="w-full p-3 rounded-lg bg-black/40 border border-white/20 focus:border-cyan-500 outline-none"
                      placeholder="Enter number of pages..."
                      disabled={skipPageLimit}
                    />
                    <div className="flex items-center mt-2">
                      <input
                        type="checkbox"
                        id="skipPageLimit"
                        checked={skipPageLimit}
                        onChange={(e) => setSkipPageLimit(e.target.checked)}
                        className="mr-2"
                      />
                      <label htmlFor="skipPageLimit" className="text-xs text-gray-400">No page limit (crawl all discovered pages)</label>
                    </div>
                  </div>
                </div>
                
                <div className="p-4 border border-cyan-500/30 rounded-lg bg-cyan-900/20">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="useSitemap"
                      checked={useSitemap}
                      onChange={(e) => setUseSitemap(e.target.checked)}
                      className="mr-2"
                    />
                    <label htmlFor="useSitemap" className="font-medium text-cyan-300">Use Sitemap for Comprehensive Crawling</label>
                  </div>
                  <p className="mt-2 text-sm text-gray-300">
                    When enabled, the crawler will attempt to discover and parse the website's sitemap.xml,
                    allowing it to find all published pages regardless of link structure.
                  </p>
                  <p className="mt-1 text-xs text-gray-400">
                    Recommended for complete site coverage. May discover up to 50+ pages depending on site size.
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">System Prompt</label>
                  <div className="space-y-4">
                    <select
                      value={promptType}
                      onChange={(e) => {
                        setPromptType(e.target.value);
                        if (e.target.value === 'standard') {
                          setSystemPrompt(`WEB CONTENT EXTRACTION AND PROCESSING

PRIMARY OBJECTIVE:
Extract high-quality, structured information from webpages to create a comprehensive knowledge base for retrieval augmented generation (RAG) systems.

EXTRACTION GUIDELINES:
1. METADATA EXTRACTION
   - Page title: Extract the complete, accurate title as displayed in browser tabs
   - Publication date: Identify and standardize to ISO format (YYYY-MM-DD)
   - Author information: Extract name(s) and credentials when available
   - URL: Preserve the canonical URL

2. CONTENT EXTRACTION
   - Main content: Isolate primary textual content from navigation, ads, and sidebars
   - Preserve semantic structure: Maintain heading hierarchy (H1, H2, H3, etc.)
   - Extract meaningful lists, tables, and structured data with formatting preserved
   - Remove duplicate content, navigation elements, and promotional material

3. SEMANTIC ANALYSIS
   - Identify 3-7 primary topics covered in the content
   - Extract key entities (people, organizations, products, locations)
   - Generate 3-5 relevant keywords for content categorization
   - Summarize the main content in 2-3 concise paragraphs

4. LINK PROCESSING
   - Validate all extracted links with HTTP status code checking
   - Only include links returning 200 status codes
   - Categorize links as: internal navigation, external references, citation sources
   - Prioritize links to authoritative sources or supporting documentation

5. CONTENT VERIFICATION
   - Flag potential misinformation or factually questionable content
   - Note content currency/freshness based on publication date
   - Document access limitations (paywalls, login requirements)

6. OUTPUT FORMATTING
   - Structure all extracted data in consistent JSON format
   - Ensure UTF-8 encoding for all text content
   - Preserve important formatting (bold, italics, lists) using markdown
   - Include metadata about extraction process (timestamp, version)

PROCESSING CONSTRAINTS:
- Process each page as standalone content while preserving context
- Document any extraction failures or limitations encountered

ERROR HANDLING:
- Gracefully handle malformed HTML, JavaScript-dependent content
- Record partial extractions when complete processing fails
- Provide detailed error logs for debugging and system improvement`);
                        } else {
                          setSystemPrompt(customPrompt);
                        }
                      }}
                      className="w-full p-3 rounded-lg bg-black/40 border border-white/20 focus:border-cyan-500 outline-none"
                    >
                      <option value="standard">Standard RAG Prompt</option>
                      <option value="custom">Custom Prompt</option>
                    </select>
                    
                    {promptType === 'custom' && (
                      <textarea
                        value={customPrompt}
                        onChange={(e) => {
                          setCustomPrompt(e.target.value);
                          setSystemPrompt(e.target.value);
                        }}
                        placeholder="Enter your custom prompt..."
                        rows={4}
                        className="w-full p-3 rounded-lg bg-black/40 border border-white/20 focus:border-cyan-500 outline-none resize-none font-mono text-sm"
                      />
                    )}
                  </div>
                  <p className="text-xs text-gray-400 mt-1">
                    {promptType === 'standard' ? 
                      'Using standard RAG-optimized extraction prompt' : 
                      'Using custom extraction prompt'}
                  </p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-1 gap-6">
                  <div>
                    <label className="block text-sm font-medium mb-2">LLM Model (Ollama)</label>
                    <select
                      value={model}
                      onChange={(e) => setModel(e.target.value)}
                      className="w-full p-3 rounded-lg bg-black/40 border border-white/20 focus:border-cyan-500 outline-none"
                      disabled={isLoadingModels}
                    >
                      {isLoadingModels ? (
                        <option>Loading models...</option>
                      ) : (
                        availableModels.map(model => (
                          <option key={model.name} value={model.name}>{model.name}</option>
                        ))
                      )}
                    </select>
                    <p className="text-xs text-gray-400 mt-1">Using Ollama LLM from your local installation</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-2">Embedding Model (Ollama)</label>
                    <select
                      value={embeddingModel}
                      onChange={(e) => setEmbeddingModel(e.target.value)}
                      className="w-full p-3 rounded-lg bg-black/40 border border-white/20 focus:border-cyan-500 outline-none"
                    >
                      <option value="snowflake-arctic-embed2">snowflake-arctic-embed2 (Recommended)</option>
                      <option value="nomic-embed-text">nomic-embed-text (Alternative)</option>
                    </select>
                    <p className="text-xs text-gray-400 mt-1">
                      <span className={embeddingModel === 'snowflake-arctic-embed2' ? 'text-green-400' : 'text-gray-400'}>
                        {embeddingModel === 'snowflake-arctic-embed2' 
                          ? '✓ Proven to work with 90+ pages' 
                          : 'Alternative model, may have different performance characteristics'}
                      </span>
                    </p>
                  </div>
                </div>
                
                <button
                  onClick={() => setActiveTab('crawl')}
                  className="flex items-center justify-center gap-2 py-3 px-6 bg-cyan-600 hover:bg-cyan-700 rounded-lg font-medium transition-colors duration-200"
                >
                  Next
                  <ArrowRight size={16} />
                </button>
              </div>
            )}
            
            {activeTab === 'crawl' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold mb-4">Start Crawling</h2>
                
                {error && (
                  <div className="p-4 mb-4 border border-red-500/30 rounded-lg bg-red-900/20">
                    <h3 className="font-medium text-red-300 mb-2">Error</h3>
                    <p className="text-gray-300">{error}</p>
                    
                    {(typeof error === 'string' && (error.includes('API server') || error.includes('crawler'))) && (
                      <div className="mt-3 pt-3 border-t border-red-500/30">
                        <h4 className="font-medium text-red-300 mb-1">Troubleshooting Steps:</h4>
                        <ul className="list-disc pl-5 text-sm text-gray-300">
                          <li className="mb-1">Make sure the API server is running with <code className="bg-black/30 px-1 py-0.5 rounded">python api_server.py</code></li>
                          <li className="mb-1">Verify that port 8000 is not in use by another application</li>
                          <li className="mb-1">Ensure that Ollama is running and models are available</li>
                          <li className="mb-1">Check that <code className="bg-black/30 px-1 py-0.5 rounded">deepcrawler.py</code> exists and is correctly implemented</li>
                          <li className="mb-1">Check your browser console for more detailed error messages</li>
                        </ul>
                      </div>
                    )}
                  </div>
                )}
                
                <div className="p-4 border border-white/20 rounded-lg bg-black/40">
                  <h3 className="font-medium">Configuration Summary</h3>
                  <ul className="mt-2 space-y-1 text-sm text-gray-300">
                    <li><span className="font-medium text-white">URL:</span> {url || 'Not set'}</li>
                    <li><span className="font-medium text-white">Depth:</span> {maxDepth}</li>
                    <li><span className="font-medium text-white">Max Pages:</span> {skipPageLimit ? 'No limit (crawl all pages)' : maxPages}</li>
                    <li><span className="font-medium text-white">Use Sitemap:</span> {useSitemap ? 'Yes' : 'No'}</li>
                    <li><span className="font-medium text-white">LLM Model:</span> {model}</li>
                    <li><span className="font-medium text-white">Embedding Model:</span> {embeddingModel} 
                      <span className={embeddingModel === 'snowflake-arctic-embed2' ? 'text-green-400 ml-2 text-xs' : 'text-gray-400 ml-2 text-xs'}>
                        {embeddingModel === 'snowflake-arctic-embed2' ? '(Recommended)' : '(Alternative)'}
                      </span>
                    </li>
                    <li className="mt-2"><span className="font-medium text-white">System Prompt:</span></li>
                    <li className="pl-2 italic text-xs border-l-2 border-gray-700 my-1 py-1">{systemPrompt}</li>
                  </ul>
                </div>
                
                <button
                  onClick={handleCrawl}
                  disabled={isLoading || !url}
                  className={`
                    flex items-center justify-center gap-2 py-3 px-6 rounded-lg font-medium transition-all duration-200 w-full
                    ${isLoading || !url ? 'bg-gray-600 cursor-not-allowed' : 'bg-cyan-600 hover:bg-cyan-700'}
                  `}
                >
                  {isLoading ? 'Crawling...' : 'Start Crawling'}
                  <Search size={16} />
                </button>
                
                {/* Progress Logs Display */}
                {isLoading && (
                  <div className="mt-4">
                    <h3 className="font-medium mb-2">Crawl Progress</h3>
                    <div className="border border-white/20 rounded-lg bg-black/40 p-4 h-96 overflow-y-auto font-mono text-sm">
                      {progressLogs.length > 0 ? (
                        <>
                          <div className="sticky top-0 bg-black/80 p-2 mb-2 border-b border-white/10 rounded-t flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-cyan-500"></div>
                              <span className="text-cyan-400 font-semibold">
                                {currentStatus || 'Processing...'}
                              </span>
                            </div>
                            <div className="flex items-center gap-3">
                              <span className="text-xs bg-gray-800 px-2 py-1 rounded text-gray-300">
                                Elapsed: {formatTime(elapsedTime)}
                              </span>
                              <span className="text-xs text-gray-400">{progressLogs.length} log entries</span>
                            </div>
                          </div>
                          {progressLogs.map((log, index) => {
                            // Check if this is a terminal output message
                            const isTerminalOutput = log.startsWith('[Terminal]');
                            const logContent = isTerminalOutput ? log.substring('[Terminal]'.length).trim() : log;
                            
                            // Highlight crawler messages
                            const isCrawlerMessage = logContent.startsWith('CRAWLER:');
                            const crawlerContent = isCrawlerMessage ? logContent.substring('CRAWLER:'.length).trim() : logContent;
                            
                            return (
                              <div key={index} className="mb-1">
                                {isTerminalOutput ? (
                                  // Style terminal output differently
                                  <div className="pl-2 border-l-2 border-gray-600">
                                    <span className="text-gray-400 text-xs">[Terminal] </span>
                                    <span className={isCrawlerMessage ? "text-green-400" : "text-gray-300"}>
                                      {isCrawlerMessage ? crawlerContent : logContent}
                                    </span>
                                  </div>
                                ) : (
                                  // Regular log message
                                  <div>
                                    <span className="text-cyan-400">&gt; </span>
                                    <span>{log}</span>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                          <div ref={logsEndRef} />
                        </>
                      ) : (
                        <div className="flex flex-col items-center justify-center h-full text-gray-400">
                          <span className="mb-3 text-lg font-medium">{currentStatus || 'Initializing crawler...'}</span>
                          <div className="mb-4 animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-cyan-500"></div>
                          <p className="text-sm text-gray-300 mt-2">Connecting to API server and starting crawl process</p>
                          <div className="mt-3 text-sm text-cyan-300">
                            Elapsed time: {formatTime(elapsedTime)}
                          </div>
                          <p className="text-xs text-gray-500 mt-4">If you don't see logs within 30 seconds, check the console for details.</p>
                          <p className="text-xs text-gray-500 mt-1">Crawling may take several minutes for complex sites.</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {!isLoading && progressLogs.length > 0 && (
                  <div className="mt-4">
                    <h3 className="font-medium mb-2">Crawl Logs</h3>
                    <div className="border border-white/20 rounded-lg bg-black/40 p-4 h-96 overflow-y-auto font-mono text-sm">
                      {progressLogs.map((log, index) => {
                        // Check if this is a terminal output message
                        const isTerminalOutput = log.startsWith('[Terminal]');
                        const logContent = isTerminalOutput ? log.substring('[Terminal]'.length).trim() : log;
                        
                        // Highlight crawler messages
                        const isCrawlerMessage = logContent.startsWith('CRAWLER:');
                        const crawlerContent = isCrawlerMessage ? logContent.substring('CRAWLER:'.length).trim() : logContent;
                        
                        return (
                          <div key={index} className="mb-1">
                            {isTerminalOutput ? (
                              // Style terminal output differently
                              <div className="pl-2 border-l-2 border-gray-600">
                                <span className="text-gray-400 text-xs">[Terminal] </span>
                                <span className={isCrawlerMessage ? "text-green-400" : "text-gray-300"}>
                                  {isCrawlerMessage ? crawlerContent : logContent}
                                </span>
                              </div>
                            ) : (
                              // Regular log message
                              <div>
                                <span className="text-cyan-400">&gt; </span>
                                <span>{log}</span>
                              </div>
                            )}
                          </div>
                        );
                      })}
                      <div ref={logsEndRef} />
                    </div>
                  </div>
                )}
                
                {results && !isLoading && (
                  <div className="mt-6">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="font-medium">Crawl Results</h3>
                      <button
                        onClick={() => setActiveTab('results')}
                        className="text-sm text-cyan-400 hover:text-cyan-300"
                      >
                        View Full Results
                      </button>
                    </div>
                    
                    <div className="p-4 border border-white/20 rounded-lg bg-black/40">
                      <p><span className="font-medium">Status:</span> {results.status}</p>
                      <p><span className="font-medium">Pages Crawled:</span> {results.crawl_info?.pages_crawled || results.pages?.length || 0}</p>
                      <p><span className="font-medium">Depth:</span> {results.crawl_info?.depth || maxDepth}</p>
                      <p><span className="font-medium">Stored in Database:</span> {results.vectorized ? 'Yes' : 'No'}</p>
                      
                      {results.error && (
                        <div className="mt-4 p-3 bg-red-900/50 text-red-200 rounded-lg">
                          <p className="font-medium">Error:</p>
                          <p>{results.error}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
            
            {activeTab === 'results' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold mb-4">Crawl Results</h2>
                
                {!results ? (
                  <div className="p-6 border border-white/20 rounded-lg bg-black/40 text-center">
                    <p className="text-gray-400">No results available. Start a crawl first.</p>
                  </div>
                ) : results.error ? (
                  <div className="p-4 border border-red-500/30 rounded-lg bg-red-900/20">
                    <h3 className="font-medium text-red-300 mb-2">Error</h3>
                    <p className="text-gray-300">{results.error}</p>
                    
                    {/* Display logs even on error */}
                    {progressLogs.length > 0 && (
                      <div className="mt-4">
                        <h3 className="font-medium text-gray-300 mb-2">Process Logs</h3>
                        <div className="border border-white/10 rounded-lg bg-black/40 p-4 max-h-96 overflow-y-auto font-mono text-sm">
                          {progressLogs.map((log, index) => {
                            // Check if this is a terminal output message
                            const isTerminalOutput = log.startsWith('[Terminal]');
                            const logContent = isTerminalOutput ? log.substring('[Terminal]'.length).trim() : log;
                            
                            // Highlight crawler messages
                            const isCrawlerMessage = logContent.startsWith('CRAWLER:');
                            const crawlerContent = isCrawlerMessage ? logContent.substring('CRAWLER:'.length).trim() : logContent;
                            
                            return (
                              <div key={index} className="mb-1">
                                {isTerminalOutput ? (
                                  // Style terminal output differently
                                  <div className="pl-2 border-l-2 border-gray-600">
                                    <span className="text-gray-400 text-xs">[Terminal] </span>
                                    <span className={isCrawlerMessage ? "text-green-400" : "text-gray-300"}>
                                      {isCrawlerMessage ? crawlerContent : logContent}
                                    </span>
                                  </div>
                                ) : (
                                  // Regular log message
                                  <div>
                                    <span className="text-cyan-400">&gt; </span>
                                    <span>{log}</span>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                          <div ref={logsEndRef} />
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="p-4 border border-white/20 rounded-lg bg-black/40">
                      <h3 className="font-medium mb-2">Summary</h3>
                      <p><span className="font-medium">Status:</span> {results.status}</p>
                      <p><span className="font-medium">Pages Crawled:</span> {results.pages_count || 0}</p>
                      
                      {/* Display logs in results view */}
                      {progressLogs.length > 0 && (
                        <div className="mt-4">
                          <h4 className="font-medium mb-2">Process Logs</h4>
                          <div className="border border-white/10 rounded-lg bg-black/60 p-3 max-h-60 overflow-y-auto font-mono text-xs">
                            {progressLogs.map((log, index) => {
                              // Check if this is a terminal output message
                              const isTerminalOutput = log.startsWith('[Terminal]');
                              const logContent = isTerminalOutput ? log.substring('[Terminal]'.length).trim() : log;
                              
                              // Highlight crawler messages
                              const isCrawlerMessage = logContent.startsWith('CRAWLER:');
                              const crawlerContent = isCrawlerMessage ? logContent.substring('CRAWLER:'.length).trim() : logContent;
                              
                              return (
                                <div key={index} className="mb-1">
                                  {isTerminalOutput ? (
                                    // Style terminal output differently
                                    <div className="pl-2 border-l-2 border-gray-600">
                                      <span className="text-gray-400 text-xs">[Terminal] </span>
                                      <span className={isCrawlerMessage ? "text-green-400" : "text-gray-300"}>
                                        {isCrawlerMessage ? crawlerContent : logContent}
                                      </span>
                                    </div>
                                  ) : (
                                    // Regular log message
                                    <div>
                                      <span className="text-cyan-400">&gt; </span>
                                      <span>{log}</span>
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                            <div ref={logsEndRef} />
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <div>
                      <h3 className="font-medium mb-2">Crawled Pages ({results.results?.length || 0})</h3>
                      
                      {!results.results || results.results.length === 0 ? (
                        <div className="text-center py-8 bg-black/40 rounded-lg border border-white/20">
                          <p className="text-gray-400">No pages were successfully crawled.</p>
                        </div>
                      ) : (
                        <div className="space-y-4 pr-2">
                          {results.results.map((page: any, i: number) => (
                            <div key={i} className="p-4 border border-white/20 rounded-lg bg-black/40">
                              <h4 className="font-semibold text-lg">{page.title || 'No Title'}</h4>
                              <p className="text-sm text-cyan-400 mb-2">{page.url}</p>
                              
                              <div className="mt-4">
                                <h5 className="text-sm font-medium mb-1">Content Summary</h5>
                                <div className="p-3 bg-black/60 rounded border border-white/10 text-sm">
                                  <p className="mt-1 whitespace-pre-wrap bg-black/30 p-2 rounded max-h-40 overflow-y-auto">
                                    {page.content_summary || 'No summary available'}
                                  </p>
                                  
                                  {page.content_topics && page.content_topics.length > 0 && (
                                    <div className="mt-4">
                                      <p className="font-medium">Topics:</p>
                                      <div className="flex flex-wrap gap-2 mt-1">
                                        {page.content_topics.map((topic: string, i: number) => (
                                          <span key={i} className="px-2 py-1 bg-blue-900/40 text-blue-200 rounded text-xs">
                                            {topic}
                                          </span>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                  
                                  <div className="mt-4 grid grid-cols-2 gap-4">
                                    <div>
                                      <p className="font-medium">Word Count:</p>
                                      <p className="mt-1">{page.word_count || 'N/A'}</p>
                                    </div>
                                    <div>
                                      <p className="font-medium">Chunks:</p>
                                      <p className="mt-1">{page.chunk_count || 'N/A'}</p>
                                    </div>
                                  </div>
                                  
                                  {page.embedding_length > 0 && (
                                    <div className="mt-4">
                                      <p className="font-medium">Embedding:</p>
                                      <p className="mt-1">Vector dimensions: {page.embedding_length}</p>
                                    </div>
                                  )}
                                  
                                  {page.links && page.links.length > 0 && (
                                    <div className="mt-4">
                                      <p className="font-medium">Links ({page.links.length}):</p>
                                      <details className="mt-1">
                                        <summary className="cursor-pointer text-sm text-cyan-400 hover:text-cyan-300">
                                          Show links
                                        </summary>
                                        <div className="p-2 bg-black/30 rounded mt-2 max-h-40 overflow-y-auto">
                                          <ul className="list-disc pl-5 text-xs">
                                            {page.links.slice(0, 20).map((link: string, i: number) => (
                                              <li key={i} className="mb-1 break-all">{link}</li>
                                            ))}
                                            {page.links.length > 20 && (
                                              <li className="text-gray-400">
                                                ...and {page.links.length - 20} more links
                                              </li>
                                            )}
                                          </ul>
                                        </div>
                                      </details>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
            
            {activeTab === 'chat' && (
              <div className="flex flex-col h-[600px]">
                <h2 className="text-xl font-semibold mb-4">Chat with Knowledge Base</h2>
                
                {!results ? (
                  <div className="text-center py-12 flex-1">
                    <p className="text-gray-400">No knowledge base available. Start a crawl first.</p>
                  </div>
                ) : (
                  <>
                    <div className="flex-1 overflow-y-auto border border-white/20 rounded-lg p-4 mb-4 bg-black/40">
                      {chatMessages.length === 0 ? (
                        <div className="h-full flex items-center justify-center text-gray-400">
                          <p>Ask a question about the crawled content</p>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          {chatMessages.map((msg, i) => (
                            <div 
                              key={i} 
                              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                              <div 
                                className={`
                                  max-w-[80%] p-3 rounded-lg
                                  ${msg.role === 'user' 
                                    ? 'bg-cyan-600 text-white rounded-br-none' 
                                    : 'bg-gray-700 text-white rounded-bl-none'}
                                `}
                              >
                                {msg.content}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        placeholder="Ask a question about the crawled content..."
                        className="w-full p-3 rounded-lg bg-black/40 border border-white/20 focus:border-cyan-500 outline-none"
                        onKeyDown={(e) => e.key === 'Enter' && handleChat()}
                      />
                      <button
                        onClick={handleChat}
                        className="p-3 bg-cyan-600 hover:bg-cyan-700 rounded-lg transition-colors duration-200"
                      >
                        <Send size={18} />
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
} 