'use client';

import { useState } from 'react';
import SpaceTravelEffect from '@/components/SpaceTravelEffect';

export default function CrawlTestPage() {
  const [url, setUrl] = useState('https://docs.crawl4ai.com');
  const [depth, setDepth] = useState(2);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  
  const handleCrawl = async () => {
    setIsLoading(true);
    setResult(null);
    
    try {
      const response = await fetch('/api/crawler', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url, depth })
      });
      
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error crawling URL:', error);
      setResult({ error: 'Failed to crawl the URL' });
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen w-full relative">
      <SpaceTravelEffect />
      
      <div className="container mx-auto py-16 px-4 relative z-10">
        <h1 className="text-4xl font-bold mb-8 text-white">Web Crawler Test</h1>
        
        <div className="bg-black/50 backdrop-blur-sm rounded-lg p-6 border border-white/20">
          <div className="mb-6">
            <label className="block text-white mb-2">URL to Crawl</label>
            <input 
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full p-3 bg-black/70 border border-gray-600 rounded text-white"
              placeholder="https://example.com"
            />
          </div>
          
          <div className="mb-6">
            <label className="block text-white mb-2">Crawl Depth</label>
            <select
              value={depth}
              onChange={(e) => setDepth(parseInt(e.target.value))}
              className="w-full p-3 bg-black/70 border border-gray-600 rounded text-white"
            >
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
            </select>
          </div>
          
          <button
            onClick={handleCrawl}
            disabled={isLoading}
            className={`py-3 px-6 rounded-lg ${
              isLoading 
                ? 'bg-gray-600 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700'
            } text-white font-medium transition-colors`}
          >
            {isLoading ? 'Crawling...' : 'Start Crawling'}
          </button>
        </div>
        
        {result && (
          <div className="mt-8 bg-black/50 backdrop-blur-sm rounded-lg p-6 border border-white/20">
            <h2 className="text-2xl font-bold mb-4 text-white">Results</h2>
            
            {result.error ? (
              <div className="p-4 bg-red-900/50 text-red-200 rounded-lg">
                {result.error}
              </div>
            ) : (
              <div className="space-y-6">
                <div>
                  <h3 className="text-xl font-semibold text-white">URL Information</h3>
                  <p className="text-gray-300">{result.url}</p>
                  
                  <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-3 bg-gray-900/70 rounded">
                      <p className="font-medium text-white">DNS: {result.verification?.dns?.status}</p>
                      {result.verification?.dns?.ip && (
                        <p className="text-gray-400">IP: {result.verification.dns.ip}</p>
                      )}
                    </div>
                    
                    <div className="p-3 bg-gray-900/70 rounded">
                      <p className="font-medium text-white">HTTP: {result.verification?.http?.status}</p>
                      {result.verification?.http?.headers && (
                        <p className="text-gray-400">
                          Content Type: {result.verification.http.headers.contentType}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-xl font-semibold text-white">Page Metadata</h3>
                  <div className="mt-2 space-y-2">
                    <p><span className="text-gray-400">Title:</span> {result.meta?.title}</p>
                    <p><span className="text-gray-400">H1:</span> {result.meta?.h1}</p>
                    <p><span className="text-gray-400">Description:</span> {result.meta?.description}</p>
                    <p><span className="text-gray-400">Word Count:</span> {result.meta?.wordCount}</p>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-xl font-semibold text-white">LLM Extraction</h3>
                  <div className="mt-2 p-4 bg-gray-900/70 rounded-lg">
                    <p className="mb-2"><span className="text-gray-400">Title:</span> {result.content?.extracted?.title}</p>
                    <p className="mb-2"><span className="text-gray-400">Summary:</span> {result.content?.extracted?.summary}</p>
                    
                    <div className="mb-2">
                      <p className="text-gray-400">Key Points:</p>
                      <ul className="list-disc pl-5 mt-1">
                        {result.content?.extracted?.key_points?.map((point: string, i: number) => (
                          <li key={i}>{point}</li>
                        ))}
                      </ul>
                    </div>
                    
                    <div className="mb-2">
                      <p className="text-gray-400">Topics:</p>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {result.content?.extracted?.topics?.map((topic: string, i: number) => (
                          <span key={i} className="px-2 py-1 bg-blue-900/50 text-blue-200 rounded text-sm">
                            {topic}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-xl font-semibold text-white">Found Links</h3>
                  <ul className="mt-2 space-y-1">
                    {result.links?.map((link: string, i: number) => (
                      <li key={i} className="truncate">
                        <a 
                          href={link} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:text-blue-300 hover:underline"
                        >
                          {link}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 