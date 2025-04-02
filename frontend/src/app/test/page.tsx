'use client';

import { useEffect } from 'react';
import SpaceTravelEffect from '@/components/SpaceTravelEffect';

export default function TestPage() {
  useEffect(() => {
    console.log('Test page loaded successfully');
  }, []);

  return (
    <div className="h-screen w-full relative overflow-hidden">
      <SpaceTravelEffect />
      <div className="absolute inset-0 flex items-center justify-center">
        <h1 className="text-4xl font-bold text-white z-10">Space Travel Effect Test</h1>
      </div>
    </div>
  );
} 