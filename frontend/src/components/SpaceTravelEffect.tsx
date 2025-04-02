'use client';

import { useEffect, useState, useRef } from 'react';

interface SpaceTravelEffectProps {
  className?: string;
}

interface Star {
  x: number;
  y: number;
  z: number;
  size: number;
  speed: number;
  color: string;
}

interface StarSpec {
  x: number;
  y: number;
  size: number;
  speed: number;
  opacity: number;
  lifespan: number;
  age: number;
}

export default function SpaceTravelEffect({ className = '' }: SpaceTravelEffectProps) {
  const [warpEffect, setWarpEffect] = useState(0);
  const [starOpacity, setStarOpacity] = useState(0);
  const [starSpeed, setStarSpeed] = useState(0);
  const [cockpitZoom, setCockpitZoom] = useState(1);
  const [cockpitBrightness, setCockpitBrightness] = useState(100);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const starsRef = useRef<Star[]>([]);
  const starSpecsRef = useRef<StarSpec[]>([]);
  const animationFrameRef = useRef<number>(0);
  const isWarpingRef = useRef<boolean>(false);
  
  // Initialize stars
  useEffect(() => {
    const initializeStars = () => {
      // Main perspective stars
      const stars: Star[] = [];
      
      // Generate stars with z-depth for perspective
      for (let i = 0; i < 200; i++) {
        // Create stars with z-position for 3D effect
        stars.push({
          // Place in 3D space
          x: (Math.random() * 2000) - 1000, // x from -1000 to 1000
          y: (Math.random() * 2000) - 1000, // y from -1000 to 1000
          z: Math.random() * 1000 + 1,      // z from 1 to 1001 (avoid z=0)
          size: Math.random() * 2 + 1,
          speed: Math.random() * 3 + 1,
          color: `rgba(${120 + Math.random() * 135}, ${170 + Math.random() * 85}, 255, 1)`
        });
      }
      
      starsRef.current = stars;
      
      // Small star specs
      const specs: StarSpec[] = [];
      for (let i = 0; i < 150; i++) {
        specs.push({
          x: Math.random() * window.innerWidth,
          y: Math.random() * window.innerHeight,
          size: Math.random() * 1.5 + 0.5,
          speed: Math.random() * 5 + 3,
          opacity: Math.random() * 0.5 + 0.3,
          lifespan: Math.random() * 100 + 50,
          age: Math.random() * 100
        });
      }
      starSpecsRef.current = specs;
    };
    
    initializeStars();
    
    // Handle window resize
    const handleResize = () => {
      if (canvasRef.current) {
        canvasRef.current.width = window.innerWidth;
        canvasRef.current.height = window.innerHeight;
      }
      initializeStars();
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  // Animation loop
  useEffect(() => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Center point of the screen (vanishing point)
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    let lastTimestamp = 0;
    const fps = 60;
    const interval = 1000 / fps;
    
    const draw = (timestamp: number) => {
      if (timestamp - lastTimestamp < interval) {
        animationFrameRef.current = requestAnimationFrame(draw);
        return;
      }
      
      lastTimestamp = timestamp;
      
      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Draw and update stars with perspective
      starsRef.current.forEach(star => {
        // Move star closer (decrease z)
        star.z -= star.speed * starSpeed;
        
        // If star is too close, reset it far away
        if (star.z <= 0) {
          star.x = (Math.random() * 2000) - 1000;
          star.y = (Math.random() * 2000) - 1000;
          star.z = 1000; // Reset to far distance
          star.size = Math.random() * 2 + 1;
        }
        
        // Project 3D position to 2D screen
        // As z gets smaller, the star gets closer and moves away from center
        const scale = 400 / star.z;
        const x2d = centerX + star.x * scale;
        const y2d = centerY + star.y * scale;
        
        // Previous position (for trails)
        const prevZ = star.z + star.speed * starSpeed;
        const prevScale = 400 / prevZ;
        const prevX2d = centerX + star.x * prevScale;
        const prevY2d = centerY + star.y * prevScale;
        
        // Size increases as star gets closer
        const projectedSize = Math.min(5, star.size * scale);
        
        // Opacity increases as star gets closer
        const opacity = starOpacity * Math.min(1, (1000 - star.z) / 1000);
        
        // Draw the star
        if (isWarpingRef.current) {
          // During warp: draw streaks
          const length = Math.min(20, 50 / star.z * starSpeed);
          
          // Create gradient for streak
          const gradient = ctx.createLinearGradient(x2d, y2d, prevX2d, prevY2d);
          const baseColor = star.color.replace('1)', `${opacity})`);
          const fadeColor = star.color.replace('1)', '0)');
          gradient.addColorStop(0, baseColor);
          gradient.addColorStop(1, fadeColor);
          
          ctx.beginPath();
          ctx.strokeStyle = gradient;
          ctx.lineWidth = projectedSize;
          ctx.moveTo(x2d, y2d);
          ctx.lineTo(prevX2d, prevY2d);
          ctx.stroke();
        } else {
          // Normal stars: just dots
          ctx.beginPath();
          ctx.fillStyle = star.color.replace('1)', `${opacity})`);
          ctx.arc(x2d, y2d, projectedSize, 0, Math.PI * 2);
          ctx.fill();
        }
      });
      
      // Draw and update small star specs
      starSpecsRef.current.forEach((spec, index) => {
        // Update star specs
        spec.x -= spec.speed * (isWarpingRef.current ? 3 : 1);
        spec.age += 1;
        
        // Calculate flash effect - make them twinkle
        const flashOpacity = spec.opacity * (0.7 + 0.3 * Math.sin(spec.age / 10));
        
        // Reset if off-screen or past lifespan
        if (spec.x < 0 || spec.age > spec.lifespan) {
          spec.x = canvas.width;
          spec.y = Math.random() * canvas.height;
          spec.size = Math.random() * 1.5 + 0.5;
          spec.opacity = Math.random() * 0.5 + 0.3;
          spec.lifespan = Math.random() * 100 + 50;
          spec.age = 0;
        }
        
        // Draw star spec
        ctx.beginPath();
        ctx.fillStyle = `rgba(255, 255, 255, ${flashOpacity * starOpacity})`;
        ctx.arc(spec.x, spec.y, spec.size, 0, Math.PI * 2);
        ctx.fill();
        
        // During warp, occasionally add a small streak
        if (isWarpingRef.current && Math.random() < 0.1) {
          ctx.beginPath();
          ctx.strokeStyle = `rgba(255, 255, 255, ${flashOpacity * starOpacity * 0.7})`;
          ctx.lineWidth = spec.size * 0.8;
          ctx.moveTo(spec.x, spec.y);
          ctx.lineTo(spec.x + (spec.speed * 3), spec.y);
          ctx.stroke();
        }
        
        starSpecsRef.current[index] = spec;
      });
      
      animationFrameRef.current = requestAnimationFrame(draw);
    };
    
    animationFrameRef.current = requestAnimationFrame(draw);
    
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [starOpacity, starSpeed]);
  
  // Set up the warp sequence
  useEffect(() => {
    const warpSequence = () => {
      // Cycle between normal and warp speeds
      isWarpingRef.current = !isWarpingRef.current;
      
      if (isWarpingRef.current) {
        // Start warp sequence
        // Fade in stars
        const fadeInStars = setInterval(() => {
          setStarOpacity(prev => {
            if (prev >= 0.8) {
              clearInterval(fadeInStars);
              return 0.8;
            }
            return prev + 0.05;
          });
        }, 100);
        
        // Increase star speed
        const accelerateStars = setInterval(() => {
          setStarSpeed(prev => {
            if (prev >= 6) {
              clearInterval(accelerateStars);
              return 6;
            }
            return prev + 0.3;
          });
        }, 100);
        
        // Subtle zoom effect on cockpit
        const zoomCockpit = setInterval(() => {
          setCockpitZoom(prev => {
            if (prev >= 1.03) {
              clearInterval(zoomCockpit);
              return 1.03;
            }
            return prev + 0.001;
          });
          
          setCockpitBrightness(prev => {
            if (prev <= 80) {
              clearInterval(zoomCockpit);
              return 80;
            }
            return prev - 1;
          });
        }, 100);
        
        // Set warp effect
        setWarpEffect(0.3);
      } else {
        // End warp sequence
        // Fade out stars
        const fadeOutStars = setInterval(() => {
          setStarOpacity(prev => {
            if (prev <= 0.3) {
              clearInterval(fadeOutStars);
              return 0.3;
            }
            return prev - 0.05;
          });
        }, 100);
        
        // Decrease star speed
        const decelerateStars = setInterval(() => {
          setStarSpeed(prev => {
            if (prev <= 1) {
              clearInterval(decelerateStars);
              return 1;
            }
            return prev - 0.3;
          });
        }, 100);
        
        // Reset zoom effect on cockpit
        const resetZoom = setInterval(() => {
          setCockpitZoom(prev => {
            if (prev <= 1) {
              clearInterval(resetZoom);
              return 1;
            }
            return prev - 0.001;
          });
          
          setCockpitBrightness(prev => {
            if (prev >= 100) {
              clearInterval(resetZoom);
              return 100;
            }
            return prev + 1;
          });
        }, 100);
        
        // Reset warp effect
        setWarpEffect(0);
      }
    };
    
    // Initial values
    setStarOpacity(0.3);
    setStarSpeed(1);
    setCockpitZoom(1);
    setCockpitBrightness(100);
    
    // Start warp cycle
    const warpCycle = setInterval(warpSequence, 15000); // 15 seconds per cycle
    
    return () => clearInterval(warpCycle);
  }, []);
  
  return (
    <div className={`fixed inset-0 w-full h-full overflow-hidden -z-20 ${className}`}>
      {/* Cockpit background with animation */}
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat transition-all duration-1000"
        style={{
          backgroundImage: 'url(/images/cockpit.png)',
          transform: `scale(${cockpitZoom})`,
          filter: `brightness(${cockpitBrightness}%)`,
        }}
      />
      
      {/* Animated stars canvas */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full"
      />
      
      {/* Subtle warp effect overlay */}
      <div 
        className="absolute inset-0 bg-gradient-radial from-transparent to-blue-900/10 transition-opacity duration-1000"
        style={{ 
          opacity: warpEffect,
        }}
      />
    </div>
  );
} 