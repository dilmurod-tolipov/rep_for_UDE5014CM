import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Language } from '../types';

interface PreloaderProps {
  onComplete: () => void;
  lang?: Language;
}

/**
 * Full-screen opening film (~7 s): the Secret logo arrives, then the three brands pass by
 * in HD photos, each with its name. Plays on every page load, can be
 * skipped at any time, and is calm (no zoom/blur) for people who ask their device to reduce motion.
 */
const SLIDES = [
  { key: 'flowers', name: 'Secret Flowers', tag: { uz: 'Mualliflik guldastalari', ru: 'Авторские букеты', en: 'Signature bouquets' } },
  { key: 'plants', name: 'Green Mood', tag: { uz: 'Xona o‘simliklari', ru: 'Комнатные растения', en: 'Houseplants' } },
  { key: 'berries', name: 'Secret Berries', tag: { uz: 'Shokoladdagi qulupnaylar', ru: 'Клубника в шоколаде', en: 'Chocolate strawberries' } }
] as const;

const SKIP: Record<Language, string> = { uz: 'O‘tkazib yuborish', ru: 'Пропустить', en: 'Skip' };

// timeline, in milliseconds
const LOGO_ONLY = 1600; // logo alone on the brand colour
const SLIDE_MS = 1900; // each brand photo
const TOTAL = LOGO_ONLY + SLIDE_MS * SLIDES.length; // ~7.3 s
const EXIT_MS = 900;

const src = (k: string, w: number) => `/images/intro/${k}-${w}.webp`;

export function Preloader({ onComplete, lang = 'uz' }: PreloaderProps) {
  const [elapsed, setElapsed] = useState(0);
  const [done, setDone] = useState(false);
  const [ready, setReady] = useState(false);
  const finished = useRef(false);
  const reduce = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

  const finish = () => {
    if (finished.current) return;
    finished.current = true;
    setDone(true);
    setTimeout(onComplete, EXIT_MS);
  };

  // Preload the photos (phone or HD size); start the clock once the first one is in, or after 2.5 s at most.
  useEffect(() => {
    const w = window.innerWidth * (window.devicePixelRatio || 1) > 1200 ? 1920 : 1080;
    let started = false;
    const go = () => { if (!started) { started = true; setReady(true); } };
    SLIDES.forEach((s, i) => {
      const img = new Image();
      img.src = src(s.key, w);
      if (i === 0) { img.onload = go; img.onerror = go; }
    });
    const t = setTimeout(go, 2500);
    return () => clearTimeout(t);
  }, []);

  // Clock
  useEffect(() => {
    if (!ready) return;
    const t0 = performance.now();
    let raf = 0;
    const tick = (now: number) => {
      const e = now - t0;
      setElapsed(e);
      if (e >= TOTAL) finish();
      else raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    // safety net for throttled/background tabs
    const guard = setTimeout(finish, TOTAL + 1500);
    return () => { cancelAnimationFrame(raf); clearTimeout(guard); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready]);

  // No page scrolling underneath while the intro plays; Esc skips
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') finish(); };
    window.addEventListener('keydown', onKey);
    return () => { document.body.style.overflow = prev; window.removeEventListener('keydown', onKey); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const slideIndex = elapsed < LOGO_ONLY ? -1 : Math.min(SLIDES.length - 1, Math.floor((elapsed - LOGO_ONLY) / SLIDE_MS));
  const progress = Math.min(1, elapsed / TOTAL);

  return (
    <AnimatePresence>
      {!done && (
        <motion.div
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: EXIT_MS / 1000, ease: [0.22, 1, 0.36, 1] }}
          className="fixed inset-0 z-[100] bg-[#24141f] text-[#f5ecea] overflow-hidden select-none"
          style={{ height: '100dvh' }}
          role="presentation"
        >
          {/* Full-screen HD photos, one per brand, slow cross-fade + gentle push-in */}
          <AnimatePresence>
            {slideIndex >= 0 && (
              <motion.div
                key={SLIDES[slideIndex].key}
                className="absolute inset-0"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.9, ease: 'easeInOut' }}
              >
                <motion.img
                  src={src(SLIDES[slideIndex].key, 1920)}
                  srcSet={`${src(SLIDES[slideIndex].key, 1080)} 1080w, ${src(SLIDES[slideIndex].key, 1920)} 1920w`}
                  sizes="100vw"
                  alt=""
                  decoding="async"
                  className="absolute inset-0 w-full h-full object-cover"
                  initial={reduce ? false : { scale: 1.02 }}
                  animate={reduce ? undefined : { scale: 1.1 }}
                  transition={{ duration: (SLIDE_MS + 900) / 1000, ease: 'linear' }}
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Darkening so the logo and names always read clearly over the photos */}
          <div
            className="absolute inset-0 transition-opacity duration-700"
            style={{
              opacity: slideIndex >= 0 ? 1 : 0,
              background: 'radial-gradient(ellipse at center, rgba(20,10,17,0.35) 0%, rgba(20,10,17,0.62) 60%, rgba(20,10,17,0.85) 100%)'
            }}
          />

          {/* Logo, large and sharp (720 px source) */}
          <div className="absolute inset-0 flex items-center justify-center p-6">
            <motion.img
              src="/logo-circle.webp"
              alt="Secret — Flowers and more"
              className="w-[min(62vw,62vh,420px)] h-auto rounded-full shadow-[0_30px_80px_rgba(0,0,0,0.55)]"
              initial={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.86, filter: 'blur(12px)' }}
              animate={reduce ? { opacity: 1 } : { opacity: 1, scale: slideIndex >= 0 ? 0.78 : 1, y: slideIndex >= 0 ? '-8vh' : 0, filter: 'blur(0px)' }}
              transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
              draggable={false}
            />
          </div>

          {/* Brand name for the current photo */}
          <div className="absolute inset-x-0 bottom-[16vh] flex justify-center px-6 pointer-events-none">
            <AnimatePresence mode="wait">
              {slideIndex >= 0 && (
                <motion.div
                  key={SLIDES[slideIndex].key}
                  className="text-center"
                  initial={{ opacity: 0, y: reduce ? 0 : 18 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: reduce ? 0 : -10 }}
                  transition={{ duration: 0.6, ease: 'easeOut' }}
                >
                  <div className="font-serif text-4xl sm:text-6xl lg:text-7xl tracking-wide text-white drop-shadow-[0_4px_24px_rgba(0,0,0,0.6)]">
                    {SLIDES[slideIndex].name}
                  </div>
                  <div className="mt-2 text-xs sm:text-sm uppercase tracking-[0.35em] text-[#e8d2ce]">
                    {SLIDES[slideIndex].tag[lang]}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Progress (three segments, one per brand) and skip */}
          <div className="absolute inset-x-0 bottom-0 px-6 pb-[max(1.5rem,env(safe-area-inset-bottom))] flex items-center gap-4">
            <div className="flex-1 max-w-md mx-auto flex gap-1.5" aria-hidden="true">
              {SLIDES.map((s, i) => {
                const start = LOGO_ONLY + i * SLIDE_MS;
                const fill = Math.max(0, Math.min(1, (elapsed - start) / SLIDE_MS));
                return (
                  <div key={s.key} className="h-[3px] flex-1 rounded-full bg-white/20 overflow-hidden">
                    <div className="h-full bg-[#d7a9a3]" style={{ width: `${fill * 100}%` }} />
                  </div>
                );
              })}
            </div>
          </div>
          <button
            onClick={finish}
            className="absolute top-[max(1rem,env(safe-area-inset-top))] right-4 min-h-[44px] px-5 rounded-full bg-black/35 border border-white/25 text-white/90 text-sm font-medium hover:bg-black/55 cursor-pointer"
          >
            {SKIP[lang]}
          </button>
          <span className="sr-only">{Math.round(progress * 100)}%</span>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
