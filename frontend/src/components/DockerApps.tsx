'use client';
import Link from 'next/link';

interface DockerApp {
  name: string;
  port: string;
  url: string;
  description: string;
  internal?: boolean;
}

export default function DockerApps() {
  const apps: DockerApp[] = [
    {
      name: "RAG Crawler",
      port: "",
      url: "/crawler",
      description: "AI Web Crawler",
      internal: true
    },
    {
      name: "Supabase",
      port: "8001",
      url: "http://localhost:8001/project/default",
      description: "Database Dashboard"
    },
    {
      name: "Flowise",
      port: "3001",
      url: "http://localhost:3001",
      description: "AI Flow Builder"
    },
    {
      name: "Open WebUI",
      port: "3112",
      url: "http://localhost:3112",
      description: "Web Interface"
    },
    {
      name: "N8N",
      port: "5678",
      url: "http://localhost:5678",
      description: "Workflow Automation"
    },
    {
      name: "Qdrant",
      port: "6333",
      url: "http://localhost:6333/dashboard",
      description: "Vector Database"
    },
    {
      name: "PGAdmin",
      port: "5051",
      url: "http://localhost:5051",
      description: "Database Management"
    },
    {
      name: "Portainer",
      port: "9000",
      url: "http://localhost:9000",
      description: "Container Management"
    }
  ];

  const openAllServices = () => {
    const localServices = apps.filter(app => app.port !== "" && !app.internal);
    localServices.forEach(app => {
      window.open(app.url, '_blank');
    });
  };

  return (
    <div className="w-full h-full flex flex-col items-center justify-center pt-20">
      <div className="flex justify-center w-full px-4">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 place-items-center max-w-6xl">
          <a
            onClick={openAllServices}
            className="transform transition-all duration-300 hover:scale-110 cursor-pointer"
          >
            <div 
              className="group flex flex-col items-center justify-center rounded-lg border border-white/20 hover:border-cyan-500/50 transition-all duration-300 w-48 h-32 relative overflow-hidden"
              style={{
                backgroundImage: 'url(/images/button.png)',
                backgroundSize: 'cover',
                backgroundPosition: 'center'
              }}
            >
              <div className="relative z-10 w-full h-full flex flex-col items-center justify-center p-3 bg-black/30 hover:bg-black/20 transition-all duration-300">
                <h3 className="text-lg font-bold text-white mb-1 drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]">Open All</h3>
                <p className="text-red-500 text-xs mb-1 drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]">Launch Services</p>
                <span className="text-cyan-400 text-xs drop-shadow-[0_1px_1px_rgba(0,0,0,0.8)]">Local Apps</span>
              </div>
            </div>
          </a>
          {apps.map((app) => (
            app.internal ? (
              <Link
                key={app.name}
                href={app.url}
                className="transform transition-all duration-300 hover:scale-110"
              >
                <div 
                  className="group flex flex-col items-center justify-center rounded-lg border border-white/20 hover:border-cyan-500/50 transition-all duration-300 w-48 h-32 relative overflow-hidden"
                  style={{
                    backgroundImage: 'url(/images/button.png)',
                    backgroundSize: 'cover',
                    backgroundPosition: 'center'
                  }}
                >
                  <div className="relative z-10 w-full h-full flex flex-col items-center justify-center p-3 bg-black/30 hover:bg-black/20 transition-all duration-300">
                    <h3 className="text-lg font-bold text-white mb-1 drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]">{app.name}</h3>
                    <p className="text-red-500 text-xs mb-1 drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]">{app.description}</p>
                    <span className="text-cyan-400 text-xs drop-shadow-[0_1px_1px_rgba(0,0,0,0.8)]">Internal App</span>
                  </div>
                </div>
              </Link>
            ) : (
              <a
                key={app.name}
                href={app.url}
                target="_blank"
                rel="noopener noreferrer"
                className="transform transition-all duration-300 hover:scale-110"
              >
                <div 
                  className="group flex flex-col items-center justify-center rounded-lg border border-white/20 hover:border-cyan-500/50 transition-all duration-300 w-48 h-32 relative overflow-hidden"
                  style={{
                    backgroundImage: 'url(/images/button.png)',
                    backgroundSize: 'cover',
                    backgroundPosition: 'center'
                  }}
                >
                  <div className="relative z-10 w-full h-full flex flex-col items-center justify-center p-3 bg-black/30 hover:bg-black/20 transition-all duration-300">
                    <h3 className="text-lg font-bold text-white mb-1 drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]">{app.name}</h3>
                    <p className="text-red-500 text-xs mb-1 drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]">{app.description}</p>
                    {app.port && <span className="text-cyan-400 text-xs drop-shadow-[0_1px_1px_rgba(0,0,0,0.8)]">Port: {app.port}</span>}
                  </div>
                </div>
              </a>
            )
          ))}
        </div>
      </div>
    </div>
  );
} 