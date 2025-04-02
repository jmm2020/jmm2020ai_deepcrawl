'use client';

import { useState, useEffect } from 'react';
import SpaceTravelEffect from '@/components/SpaceTravelEffect';
import { getCrawlResults, getCrawlResultById } from '@/lib/supabase';

export default function CrawledResultsPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [results, setResults] = useState<any[]>([]);
  const [selectedResult, setSelectedResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadResults() {
      try {
        const response = await getCrawlResults();
        if (response.success) {
          setResults(response.data || []);
        } else {
          setError('Failed to load crawled results');
        }
      } catch (err) {
        console.error('Error loading results:', err);
        setError('Error connecting to database');
      } finally {
        setIsLoading(false);
      }
    }

    loadResults();
  }, []);

  const handleResultClick = async (id: string) => {
    try {
      setIsLoading(true);
      const response = await getCrawlResultById(id);
      if (response.success) {
        setSelectedResult(response.data);
      } else {
        setError('Failed to load result details');
      }
    } catch (err) {
      console.error('Error loading result details:', err);
      setError('Error fetching result details');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full relative">
      <SpaceTravelEffect />
      
      <div className="container mx-auto py-16 px-4 relative z-10">
        <h1 className="text-4xl font-bold mb-8 text-white">Crawled Results</h1>
        
        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-500 rounded-lg text-white">
            {error}
          </div>
        )}
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <div className="bg-black/50 backdrop-blur-sm rounded-lg p-6 border border-white/20">
              <h2 className="text-2xl font-bold mb-4 text-white">Results</h2>
              
              {isLoading && !selectedResult ? (
                <div className="flex justify-center p-8">
                  <div className="animate-pulse text-cyan-400">Loading results...</div>
                </div>
              ) : results.length === 0 ? (
                <div className="p-4 text-center text-gray-400">
                  No crawled URLs found in the database
                </div>
              ) : (
                <ul className="space-y-2">
                  {results.map((result) => (
                    <li 
                      key={result.id} 
                      className={`p-3 rounded-lg cursor-pointer transition-colors ${
                        selectedResult?.id === result.id 
                          ? 'bg-cyan-900/40 border border-cyan-500/50' 
                          : 'bg-gray-900/40 border border-gray-700 hover:border-gray-500'
                      }`}
                      onClick={() => handleResultClick(result.id)}
                    >
                      <div className="font-medium truncate">{result.meta?.title || result.url}</div>
                      <div className="text-sm text-gray-400 truncate">{result.url}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {new Date(result.timestamp).toLocaleString()}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
          
          <div className="lg:col-span-2">
            <div className="bg-black/50 backdrop-blur-sm rounded-lg p-6 border border-white/20">
              <h2 className="text-2xl font-bold mb-4 text-white">Details</h2>
              
              {isLoading && selectedResult ? (
                <div className="flex justify-center p-8">
                  <div className="animate-pulse text-cyan-400">Loading details...</div>
                </div>
              ) : !selectedResult ? (
                <div className="p-8 text-center text-gray-400">
                  Select a result to view details
                </div>
              ) : (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-xl font-semibold text-white">URL Information</h3>
                    <p className="text-gray-300">{selectedResult.url}</p>
                    
                    <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-3 bg-gray-900/70 rounded">
                        <p className="font-medium text-white">DNS: {selectedResult.verification?.dns?.status}</p>
                        {selectedResult.verification?.dns?.ip && (
                          <p className="text-gray-400">IP: {selectedResult.verification.dns.ip}</p>
                        )}
                      </div>
                      
                      <div className="p-3 bg-gray-900/70 rounded">
                        <p className="font-medium text-white">HTTP: {selectedResult.verification?.http?.status}</p>
                        {selectedResult.verification?.http?.headers && (
                          <p className="text-gray-400">
                            Content Type: {selectedResult.verification.http.headers.contentType}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-xl font-semibold text-white">Page Metadata</h3>
                    <div className="mt-2 space-y-2">
                      <p><span className="text-gray-400">Title:</span> {selectedResult.meta?.title}</p>
                      <p><span className="text-gray-400">H1:</span> {selectedResult.meta?.h1}</p>
                      <p><span className="text-gray-400">Description:</span> {selectedResult.meta?.description}</p>
                      <p><span className="text-gray-400">Word Count:</span> {selectedResult.meta?.wordCount}</p>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-xl font-semibold text-white">LLM Extraction</h3>
                    <div className="mt-2 p-4 bg-gray-900/70 rounded-lg">
                      <p className="mb-2"><span className="text-gray-400">Title:</span> {selectedResult.content?.extracted?.title}</p>
                      <p className="mb-2"><span className="text-gray-400">Summary:</span> {selectedResult.content?.extracted?.summary}</p>
                      
                      <div className="mb-2">
                        <p className="text-gray-400">Key Points:</p>
                        <ul className="list-disc pl-5 mt-1">
                          {selectedResult.content?.extracted?.key_points?.map((point: string, i: number) => (
                            <li key={i}>{point}</li>
                          ))}
                        </ul>
                      </div>
                      
                      <div className="mb-2">
                        <p className="text-gray-400">Topics:</p>
                        <div className="flex flex-wrap gap-2 mt-1">
                          {selectedResult.content?.extracted?.topics?.map((topic: string, i: number) => (
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
                      {selectedResult.links?.map((link: string, i: number) => (
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
          </div>
        </div>
      </div>
    </div>
  );
} 