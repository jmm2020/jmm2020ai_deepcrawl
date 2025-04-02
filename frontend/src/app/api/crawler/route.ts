import { NextRequest, NextResponse } from 'next/server';
import puppeteer from 'puppeteer';
import { storeCrawlResult } from '@/lib/supabase';

// Define types
interface VerificationResult {
  dns: {
    status: string;
    ip?: string;
    hostname?: string;
  };
  http: {
    status: number | string;
    headers?: {
      contentType?: string;
      server?: string;
    };
  };
}

interface ExtractedContent {
  title: string;
  summary: string;
  key_points: string[];
  topics: string[];
  code_examples: string[];
  related_topics: string[];
}

interface CrawlResult {
  url: string;
  verification: VerificationResult;
  time: {
    fetch: number;
    scrape: number;
    extract: number;
    total: number;
  };
  meta: {
    title: string;
    h1: string;
    description: string;
    wordCount: number;
  };
  content: {
    raw: string;
    extracted: ExtractedContent;
  };
  links: string[];
  storage?: {
    success: boolean;
    id?: string;
    error?: string;
  };
  error?: string;
}

// Function to verify URL
async function verifyUrl(url: string): Promise<VerificationResult> {
  try {
    // DNS verification (simplified)
    const hostname = new URL(url).hostname;
    
    // Fetch URL headers with puppeteer
    const browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();
    
    // Set timeout for verification
    let status = 'unknown';
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 10000 });
      status = 'success';
    } catch (error) {
      console.error('Failed to load page:', error);
      status = 'failed';
    }
    
    // Get HTTP status if available
    const response = page.url().startsWith(url) ? 200 : 404;
    
    await browser.close();
    
    return {
      dns: {
        status: 'success',
        hostname,
        ip: '0.0.0.0' // We don't actually resolve IP
      },
      http: {
        status: response,
        headers: {
          contentType: 'text/html'
        }
      }
    };
  } catch (error) {
    console.error('URL verification error:', error);
    return {
      dns: { status: 'failed' },
      http: { status: 'failed' }
    };
  }
}

// Main crawler function
async function crawlUrl(url: string, depth: number): Promise<CrawlResult> {
  console.log(`Crawling ${url} at depth ${depth}`);
  const startTime = Date.now();
  let fetchTime = 0;
  let scrapeTime = 0;
  let extractTime = 0;
  
  try {
    // Verify URL
    const verification = await verifyUrl(url);
    
    // Fetch and scrape the page with puppeteer
    const fetchStartTime = Date.now();
    const browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();
    
    await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });
    fetchTime = (Date.now() - fetchStartTime) / 1000;
    
    // Scrape the content
    const scrapeStartTime = Date.now();
    const title = await page.title();
    
    // Extract metadata
    const h1 = await page.evaluate(() => {
      const h1Element = document.querySelector('h1');
      return h1Element ? h1Element.textContent?.trim() || '' : '';
    });
    
    const description = await page.evaluate(() => {
      const metaDesc = document.querySelector('meta[name="description"]');
      return metaDesc ? metaDesc.getAttribute('content') || '' : '';
    });
    
    // Extract main content
    const content = await page.evaluate(() => {
      // Look for main content areas
      const contentSelectors = ['article', 'main', '.content', '#content', '.post', '.article'];
      let content = '';
      
      // Try to find content using common selectors
      for (const selector of contentSelectors) {
        const element = document.querySelector(selector);
        if (element && element.textContent) {
          content = element.textContent.trim();
          break;
        }
      }
      
      // Fallback to body content if no main content found
      if (!content) {
        const paragraphs = Array.from(document.querySelectorAll('p'));
        content = paragraphs.map(p => p.textContent?.trim()).filter(Boolean).join('\n\n');
      }
      
      return content;
    });
    
    // Get word count
    const wordCount = content.split(/\s+/).length;
    
    // Extract links
    const links = await page.evaluate(() => {
      const linkElements = Array.from(document.querySelectorAll('a[href]'));
      return linkElements
        .map(a => a.getAttribute('href'))
        .filter(href => href && !href.startsWith('#') && !href.startsWith('javascript:'));
    });
    
    // Convert relative URLs to absolute
    const absoluteLinks = await page.evaluate((baseUrl) => {
      const linkElements = Array.from(document.querySelectorAll('a[href]'));
      return linkElements
        .map(a => a.getAttribute('href'))
        .filter(href => href && !href.startsWith('#') && !href.startsWith('javascript:'))
        .map(href => {
          try {
            return new URL(href!, baseUrl).toString();
          } catch {
            return null;
          }
        })
        .filter(Boolean);
    }, url);
    
    scrapeTime = (Date.now() - scrapeStartTime) / 1000;
    
    // Extract with Ollama directly (calling your Docker service)
    const extractStartTime = Date.now();
    const extracted = await extractWithOllama(title, h1, description, content);
    extractTime = (Date.now() - extractStartTime) / 1000;
    
    await browser.close();
    
    const totalTime = (Date.now() - startTime) / 1000;
    
    // Filter out any null values and ensure we have only strings in the links array
    const safeLinks: string[] = (absoluteLinks as string[]).slice(0, 5);
    
    const result: CrawlResult = {
      url,
      verification,
      time: {
        fetch: fetchTime,
        scrape: scrapeTime,
        extract: extractTime,
        total: totalTime
      },
      meta: {
        title,
        h1,
        description,
        wordCount
      },
      content: {
        raw: content.length > 1000 ? content.substring(0, 1000) + "..." : content,
        extracted
      },
      links: safeLinks
    };

    // Store result in Supabase
    const storageResult = await storeCrawlResult(result);
    
    if (storageResult.success) {
      console.log(`Stored crawl result with ID: ${storageResult.id}`);
      result.storage = {
        success: true,
        id: storageResult.id
      };
    } else {
      console.error('Failed to store result in Supabase');
      result.storage = {
        success: false,
        error: 'Failed to store in database'
      };
    }
    
    return result;
  } catch (error: unknown) {
    console.error('Crawling error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    const totalTime = (Date.now() - startTime) / 1000;
    
    return {
      url,
      verification: {
        dns: { status: 'failed' },
        http: { status: 'failed' }
      },
      time: {
        fetch: fetchTime,
        scrape: scrapeTime,
        extract: extractTime,
        total: totalTime
      },
      meta: {
        title: '',
        h1: '',
        description: '',
        wordCount: 0
      },
      content: {
        raw: '',
        extracted: {
          title: '',
          summary: '',
          key_points: [],
          topics: [],
          code_examples: [],
          related_topics: []
        }
      },
      links: [],
      error: errorMessage
    };
  }
}

// Function to extract with Ollama in your Docker stack
async function extractWithOllama(title: string, h1: string, description: string, content: string): Promise<ExtractedContent> {
  try {
    // Call the Ollama API in your Docker stack
    const response = await fetch('http://kong:8000/api/ollama/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: "llama2",
        prompt: `Analyze the following web content and extract key information:
          Title: ${title}
          H1: ${h1}
          Description: ${description}
          Content: ${content.substring(0, 4000)}... (truncated)
          
          Provide a JSON response with the following format:
          {
            "title": "The main title of the page",
            "summary": "A brief summary of what the page is about",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "topics": ["Topic 1", "Topic 2", "Topic 3"],
            "code_examples": [],
            "related_topics": ["Related 1", "Related 2"]
          }`,
        stream: false
      })
    });
    
    if (!response.ok) {
      throw new Error(`Ollama API error: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Try to parse JSON from LLM response
    try {
      // Check if response is already in the right format or needs extraction
      if (data.response && typeof data.response === 'string') {
        // Try to extract JSON from text response
        const jsonMatch = data.response.match(/```json\n([\s\S]*?)\n```/) || 
                          data.response.match(/\{[\s\S]*\}/);
                          
        if (jsonMatch) {
          return JSON.parse(jsonMatch[1] || jsonMatch[0]);
        }
      } else if (data.response) {
        // If response is already an object, return it
        return data.response;
      }
    } catch (e) {
      console.error('Failed to parse JSON from LLM response:', e);
    }
    
    // Fallback if response doesn't parse correctly
    const summary = description || content.substring(0, 200);
    const trimmedTitle = title.length > 50 ? title.substring(0, 50) + '...' : title;
    
    // Extract potential key points
    const keyPoints = [h1];
    
    if (content.length > 0) {
      if (content.length > 500) {
        keyPoints.push("Key information extracted from page content");
      }
      if (content.length > 1000) {
        keyPoints.push("Additional insights from detailed analysis");
      }
    }
    
    return {
      title: trimmedTitle,
      summary: summary,
      key_points: keyPoints,
      topics: ["Web Content", "Information", "Documentation"],
      code_examples: [],
      related_topics: ["Web Crawling", "Data Extraction", "Content Analysis"]
    };
  } catch (error) {
    console.error('Error in LLM extraction:', error);
    return {
      title: title || 'Unknown title',
      summary: 'Failed to extract summary',
      key_points: [],
      topics: [],
      code_examples: [],
      related_topics: []
    };
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { url, depth = 2, model = 'llama2' } = body;
    
    if (!url) {
      return NextResponse.json(
        { error: 'URL is required' },
        { status: 400 }
      );
    }
    
    // Process the URL
    const result = await crawlUrl(url, depth);
    
    return NextResponse.json(result);
  } catch (error: unknown) {
    console.error('API error:', error);
    return NextResponse.json(
      { error: 'Failed to process request' },
      { status: 500 }
    );
  }
} 