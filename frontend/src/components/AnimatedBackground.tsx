'use client';

import { useEffect, useState } from 'react';

interface AnimatedBackgroundProps {
  className?: string;
}

export default function AnimatedBackground({ className = '' }: AnimatedBackgroundProps) {
  const [offset, setOffset] = useState(0);
  
  useEffect(() => {
    let animationFrameId: number;
    let startTime: number;
    
    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = timestamp - startTime;
      
      // Update offset for animation
      setOffset(prev => (prev + 0.2) % 100);
      
      animationFrameId = requestAnimationFrame(animate);
    };
    
    animationFrameId = requestAnimationFrame(animate);
    
    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className={`absolute inset-0 w-full h-full overflow-hidden -z-10 ${className}`}>
      <svg
        className="absolute inset-0 w-full h-full"
        xmlns="http://www.w3.org/2000/svg"
        version="1.1"
        width="100%"
        height="100%"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="rgba(0, 20, 50, 0.5)" />
            <stop offset="50%" stopColor="rgba(0, 80, 120, 0.3)" />
            <stop offset="100%" stopColor="rgba(0, 20, 50, 0.5)" />
          </linearGradient>
          
          <pattern id="hexagons" width="56" height="100" patternUnits="userSpaceOnUse" patternTransform={`translate(${offset}, ${offset/2})`}>
            <path 
              d="M28 66L0 50L0 16L28 0L56 16L56 50L28 66L28 100" 
              fill="none" 
              stroke="rgba(0, 180, 255, 0.05)" 
              strokeWidth="1"
            />
          </pattern>
          
          <pattern id="circles" width="40" height="40" patternUnits="userSpaceOnUse" patternTransform={`translate(${-offset/2}, ${offset/3})`}>
            <circle cx="20" cy="20" r="8" fill="none" stroke="rgba(120, 220, 255, 0.05)" strokeWidth="1" />
          </pattern>
          
          <pattern id="grid" width="80" height="80" patternUnits="userSpaceOnUse" patternTransform={`translate(${offset/3}, ${-offset/4})`}>
            <path 
              d="M80 0L0 0L0 80" 
              fill="none" 
              stroke="rgba(100, 200, 255, 0.03)" 
              strokeWidth="1"
            />
          </pattern>
          
          <radialGradient id="spotlight" cx="50%" cy="50%" r="100%" fx="50%" fy="50%">
            <stop offset="0%" stopColor="rgba(0, 30, 60, 0)" />
            <stop offset="100%" stopColor="rgba(0, 10, 30, 0.4)" />
          </radialGradient>
        </defs>
        
        <rect x="0" y="0" width="100%" height="100%" fill="url(#gradient)" />
        <rect x="0" y="0" width="100%" height="100%" fill="url(#hexagons)" />
        <rect x="0" y="0" width="100%" height="100%" fill="url(#circles)" />
        <rect x="0" y="0" width="100%" height="100%" fill="url(#grid)" />
        <rect x="0" y="0" width="100%" height="100%" fill="url(#spotlight)" />
      </svg>
      
      {/* Floating particles */}
      <div className="absolute top-0 left-0 w-full h-full">
        {Array.from({ length: 20 }).map((_, i) => (
          <div
            key={i}
            className="absolute rounded-full bg-cyan-500/10"
            style={{
              width: `${Math.random() * 6 + 2}px`,
              height: `${Math.random() * 6 + 2}px`,
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
              opacity: Math.random() * 0.5 + 0.2,
              animation: `float ${Math.random() * 10 + 20}s linear infinite`,
              animationDelay: `-${Math.random() * 20}s`,
            }}
          />
        ))}
      </div>
      
      {/* Light flares */}
      <div className="absolute top-0 left-0 w-full h-full opacity-20">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="absolute rounded-full bg-gradient-to-r from-cyan-500/0 via-cyan-500/10 to-cyan-500/0"
            style={{
              width: `${Math.random() * 500 + 100}px`,
              height: `${Math.random() * 500 + 100}px`,
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
              transform: 'translate(-50%, -50%)',
              filter: 'blur(30px)',
              opacity: Math.random() * 0.3 + 0.1,
              animation: `pulse ${Math.random() * 10 + 10}s ease-in-out infinite alternate`,
              animationDelay: `-${Math.random() * 10}s`,
            }}
          />
        ))}
      </div>
    </div>
  );
} 