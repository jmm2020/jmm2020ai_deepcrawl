'use client';
import { useEffect, useState } from 'react';

export default function Hero() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  return (
    <div className="flex items-center justify-center py-8">
      <div className={`text-center transform transition-all duration-1000 ${
        isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
      }`}>
        <h1 className="text-4xl md:text-5xl font-bold text-white mb-4 tracking-tight drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]">
          Access the Power of
          <span className="block text-cyan-400 drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]">Artificial Intelligence</span>
        </h1>
        <p className="text-lg md:text-xl text-red-500 mb-4 max-w-2xl mx-auto drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]">
          Harness advanced AI models and neural networks for unprecedented capabilities
        </p>
      </div>
    </div>
  );
} 