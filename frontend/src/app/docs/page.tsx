'use client';

import Navbar from '@/components/Navbar';
import Image from 'next/image';

interface DocLink {
  name: string;
  url: string;
  description: string;
}

export default function Documents() {
  const docs: DocLink[] = [
    {
      name: "Crawl4AI",
      url: "https://docs.crawl4ai.com/",
      description: "Web Crawler & Scraper"
    },
    {
      name: "LightLLM",
      url: "https://lightllm-en.readthedocs.io/en/latest/index.html",
      description: "Fast LLM Inference Service"
    },
    {
      name: "PyTorch",
      url: "https://pytorch.org/docs/stable/index.html",
      description: "Deep Learning Framework"
    },
    {
      name: "Portainer",
      url: "https://docs.portainer.io/",
      description: "Container Management UI"
    },
    {
      name: "Qdrant",
      url: "https://qdrant.tech/documentation/",
      description: "Vector Database"
    },
    {
      name: "n8n",
      url: "https://docs.n8n.io/",
      description: "Workflow Automation Platform"
    },
    {
      name: "Playwright",
      url: "https://playwright.dev/docs/intro",
      description: "Browser Automation"
    },
    {
      name: "Ollama Docker",
      url: "https://ollama.readthedocs.io/en/docker/",
      description: "Docker Container for LLMs"
    }
  ];

  return (
    <div className="min-h-screen relative">
      <div className="fixed inset-0 z-0">
        <Image
          src="/images/library.jpg"
          alt="Library Background"
          fill
          style={{ objectFit: 'cover' }}
          quality={100}
          priority
        />
        <div className="absolute inset-0 bg-black/30" />
      </div>
      <div className="relative z-10">
        <Navbar />
        <div className="container mx-auto px-4 py-16 flex justify-center">
          <div className="w-[600px] bg-white/95 backdrop-blur-lg rounded-xl shadow-2xl p-8">
            <h1 className="text-3xl font-bold text-gray-800 mb-8 text-center">Documentation</h1>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 place-items-center">
              {docs.map((doc, index) => (
                <a
                  key={index}
                  href={doc.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="transform transition-all duration-300 hover:scale-105"
                >
                  <div 
                    className="group flex flex-col items-center justify-center rounded-lg border border-gray-200 hover:border-cyan-500/50 transition-all duration-300 w-[240px] h-[140px] relative overflow-hidden"
                    style={{
                      backgroundImage: 'url(/images/book.jpg)',
                      backgroundSize: 'cover',
                      backgroundPosition: 'center'
                    }}
                  >
                    <div className="relative z-10 w-full h-full flex flex-col items-center justify-center p-3 bg-black/30 hover:bg-black/20 transition-all duration-300">
                      <h3 className="text-lg font-bold text-white mb-1 drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]">{doc.name}</h3>
                      <p className="text-gray-100 text-xs text-center drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]">{doc.description}</p>
                    </div>
                  </div>
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 