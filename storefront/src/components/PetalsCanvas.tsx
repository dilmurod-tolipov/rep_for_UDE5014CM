import { useEffect, useRef, useState } from 'react';
import { ThemeMode } from '../types';

interface PetalsCanvasProps {
  theme: ThemeMode;
}

interface Particle {
  x: number;
  y: number;
  size: number;
  speedY: number;
  speedX: number;
  rotation: number;
  rotationSpeed: number;
  swayAmplitude: number;
  swayFrequency: number;
  swayOffset: number;
  color: string;
  opacity: number;
  type: 'petal' | 'sparkle' | 'spore';
}

// The falling-petals layer redraws the whole screen 60 times a second. That is fine on a laptop,
// but on phones it drains the battery and competes with scrolling, so it only runs on
// larger screens with a mouse, and never for people who asked their device to reduce motion.
function petalsAllowed(): boolean {
  if (typeof window === 'undefined' || !window.matchMedia) return false;
  const phoneLike = window.matchMedia('(max-width: 767px), (pointer: coarse)').matches;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  return !phoneLike && !reduceMotion;
}

export function PetalsCanvas({ theme }: PetalsCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [enabled] = useState(petalsAllowed);

  useEffect(() => {
    if (!enabled) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);

    // Mouse velocity interaction
    let mouseX = width / 2;
    let mouseY = height / 2;
    let mouseSpeedX = 0;
    let lastMouseX = width / 2;

    const handleMouseMove = (e: MouseEvent) => {
      mouseSpeedX = (e.clientX - lastMouseX) * 0.05;
      lastMouseX = e.clientX;
      mouseX = e.clientX;
      mouseY = e.clientY;
    };
    window.addEventListener('mousemove', handleMouseMove);

    const particleCount = width < 768 ? 24 : 45;
    const particles: Particle[] = [];

    const isDark = theme === 'dark';
    // Colors strictly matched to Secret logo: Dusty Rose #d7a9a3, Soft Blush #e8beb8, Velvet Plum #4a2e3f
    const petalColors = isDark
      ? ['rgba(215, 169, 163, 0.45)', 'rgba(232, 190, 184, 0.4)', 'rgba(184, 134, 128, 0.35)', 'rgba(74, 46, 63, 0.5)']
      : ['rgba(215, 169, 163, 0.55)', 'rgba(196, 143, 136, 0.5)', 'rgba(245, 236, 234, 0.7)', 'rgba(41, 24, 35, 0.25)'];

    for (let i = 0; i < particleCount; i++) {
      const type = Math.random() > 0.4 ? 'petal' : Math.random() > 0.5 ? 'sparkle' : 'spore';
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        size: type === 'petal' ? Math.random() * 8 + 6 : Math.random() * 2.5 + 1.5,
        speedY: Math.random() * 0.8 + 0.4,
        speedX: (Math.random() - 0.5) * 0.4,
        rotation: Math.random() * Math.PI * 2,
        rotationSpeed: (Math.random() - 0.5) * 0.02,
        swayAmplitude: Math.random() * 25 + 10,
        swayFrequency: Math.random() * 0.02 + 0.008,
        swayOffset: Math.random() * Math.PI * 2,
        color: petalColors[Math.floor(Math.random() * petalColors.length)],
        opacity: Math.random() * 0.5 + 0.2,
        type
      });
    }

    let time = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      time += 1;

      mouseSpeedX *= 0.95; // decay wind

      particles.forEach((p) => {
        p.y += p.speedY;
        const sway = Math.sin(time * p.swayFrequency + p.swayOffset) * 0.8;
        p.x += p.speedX + sway + mouseSpeedX;
        p.rotation += p.rotationSpeed;

        // Wrap around boundaries
        if (p.y > height + 20) {
          p.y = -20;
          p.x = Math.random() * width;
        }
        if (p.x > width + 20) p.x = -20;
        if (p.x < -20) p.x = width + 20;

        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rotation);
        ctx.globalAlpha = p.opacity;

        if (p.type === 'petal') {
          // Draw organic curved flower petal
          ctx.beginPath();
          ctx.moveTo(0, 0);
          ctx.bezierCurveTo(p.size, -p.size * 0.8, p.size * 1.5, p.size * 0.5, 0, p.size * 2);
          ctx.bezierCurveTo(-p.size * 1.5, p.size * 0.5, -p.size, -p.size * 0.8, 0, 0);
          ctx.fillStyle = p.color;
          ctx.fill();
        } else if (p.type === 'sparkle') {
          // 4-point star sparkle
          ctx.beginPath();
          const s = p.size * 2;
          ctx.moveTo(0, -s);
          ctx.quadraticCurveTo(0, 0, s, 0);
          ctx.quadraticCurveTo(0, 0, 0, s);
          ctx.quadraticCurveTo(0, 0, -s, 0);
          ctx.quadraticCurveTo(0, 0, 0, -s);
          ctx.fillStyle = isDark ? '#fef08a' : '#f59e0b';
          ctx.fill();
        } else {
          // Soft botanical pollen spore
          ctx.beginPath();
          ctx.arc(0, 0, p.size, 0, Math.PI * 2);
          ctx.fillStyle = p.color;
          ctx.fill();
        }

        ctx.restore();
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, [theme, enabled]);

  if (!enabled) return null;

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0 opacity-80"
    />
  );
}
