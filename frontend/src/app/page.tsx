'use client';

import Navbar from '@/components/Navbar';
import Hero from '@/components/Hero';
import DockerApps from '@/components/DockerApps';
import { useEffect } from 'react';

export default function Home() {
  // Ensure client-side rendering
  useEffect(() => {
    // Client-side effect to ensure hydration
  }, []);

  return (
    <main className="h-screen relative overflow-hidden">
      <Navbar />
      <div className="h-full flex flex-col">
        <div className="pt-16">
          <Hero />
        </div>
        <div className="flex-1">
          <DockerApps />
        </div>
      </div>
    </main>
  );
}
