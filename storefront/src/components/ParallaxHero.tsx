import React, { useState, useEffect } from 'react';
import { motion, useScroll, useTransform } from 'motion/react';
import { Sparkles, ArrowRight, Clock, ShieldCheck, Camera, CreditCard, Instagram } from 'lucide-react';
import { Language, ThemeMode, BrandCategory } from '../types';
import { TRANSLATIONS } from '../translations';
import { SecretLogo } from './SecretLogo';
import { soundManager } from '../utils/audio';

interface ParallaxHeroProps {
  lang: Language;
  theme: ThemeMode;
  onExploreCatalog: (brand?: BrandCategory) => void;
  onOpenAtelier: () => void;
}

export function ParallaxHero({ lang, theme, onExploreCatalog, onOpenAtelier }: ParallaxHeroProps) {
  const t = TRANSLATIONS[lang];
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  const { scrollY } = useScroll();
  const yBg = useTransform(scrollY, [0, 600], [0, 150]);

  // Handle subtle 3D mouse tracking tilt
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const { clientX, clientY, currentTarget } = e;
    const { width, height, left, top } = currentTarget.getBoundingClientRect();
    const x = (clientX - left) / width - 0.5;
    const y = (clientY - top) / height - 0.5;
    setMousePos({ x, y });
  };

  const handleMouseLeave = () => {
    setMousePos({ x: 0, y: 0 });
  };

  return (
    <div
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="relative min-h-[92vh] flex items-center justify-center pt-24 pb-16 px-4 sm:px-6 lg:px-8 overflow-hidden perspective-1000"
    >
      {/* Dynamic Background Glows matching Secret Logo Plum & Dusty Rose */}
      <motion.div
        style={{ y: yBg }}
        className="absolute inset-0 pointer-events-none overflow-hidden"
      >
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[650px] bg-gradient-to-br from-[#d7a9a3]/15 via-[#291823]/25 to-transparent rounded-full blur-[140px]" />
        <div className="absolute -top-10 -right-20 w-[450px] h-[450px] bg-[#4a2e3f]/20 rounded-full blur-[120px]" />
      </motion.div>

      <div className="relative z-10 max-w-6xl mx-auto w-full text-center flex flex-col items-center">
        {/* Luxury Official Brand Emblem */}
        <motion.div
          initial={{ opacity: 0, scale: 0.85, y: -20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="mb-7 flex flex-col items-center group cursor-pointer select-none"
          onClick={() => soundManager.playChime(720)}
        >
          <div className="relative p-1.5 rounded-full border border-[#d7a9a3]/50 bg-white/50 dark:bg-[#1a0f17]/80 shadow-[0_8px_50px_rgba(215,169,163,0.35)] group-hover:scale-[1.03] transition-transform duration-500">
            <img
              src="/logo-circle.webp"
              alt="Secret — Flowers and more"
              className="block w-36 h-36 sm:w-48 sm:h-48 lg:w-56 lg:h-56 rounded-full select-none"
              draggable={false}
            />
          </div>
        </motion.div>

        {/* Luxury Brand Eyebrow Badge */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-[#d7a9a3]/40 bg-[#d7a9a3]/10 backdrop-blur-md text-[#291823] dark:text-[#f5ecea] text-xs sm:text-sm font-medium tracking-widest uppercase mb-6"
        >
          <Sparkles className="w-3.5 h-3.5 text-[#d7a9a3] animate-spin [animation-duration:8s]" />
          <span>{t.heroBadge}</span>
          <span className="w-1 h-1 rounded-full bg-[#d7a9a3]" />
          <span className="text-xs opacity-80">{t.heroCity}</span>
        </motion.div>

        {/* 3D Interactive Main Headline */}
        <motion.div
          style={{
            transform: `rotateX(${mousePos.y * -12}deg) rotateY(${mousePos.x * 14}deg)`,
            transition: 'transform 0.15s ease-out'
          }}
          className="preserve-3d"
        >
          <h1 className="font-serif text-4xl sm:text-6xl lg:text-7xl font-light tracking-tight text-neutral-900 dark:text-[#f8f5f0] max-w-4xl mx-auto leading-[1.12] mb-6">
            {t.heroHeadA}{' '}
            <span className="italic font-normal text-transparent bg-clip-text bg-gradient-to-r from-[#d7a9a3] via-[#e8beb8] to-[#c48f88]">{t.heroHeadEm}</span>
            {t.heroHeadB ? <> {t.heroHeadB}</> : null}
          </h1>
        </motion.div>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="text-base sm:text-lg text-neutral-600 dark:text-neutral-300 max-w-2xl mx-auto font-light leading-relaxed mb-10"
        >
          {t.heroSubtitle}
        </motion.p>

        {/* Interactive CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.3 }}
          className="flex flex-wrap items-center justify-center gap-4 mb-14"
        >
          <button
            id="btn-hero-catalog"
            onClick={() => {
              soundManager.playPluck();
              onExploreCatalog();
            }}
            className="group relative px-8 py-4 rounded-full bg-[#291823] text-[#d7a9a3] dark:bg-[#d7a9a3] dark:text-[#291823] font-medium text-sm sm:text-base tracking-wide shadow-xl hover:shadow-2xl transition-all duration-300 flex items-center gap-3 cursor-pointer overflow-hidden hover:scale-[1.02] border border-[#d7a9a3]/40"
          >
            <span className="relative z-10">{t.heroOrderBtn}</span>
            <ArrowRight className="w-4 h-4 relative z-10 group-hover:translate-x-1 transition-transform" />
            <div className="absolute inset-0 bg-white/10 dark:bg-[#291823]/10 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
          </button>

          <button
            id="btn-hero-atelier"
            onClick={() => {
              soundManager.playChime(880);
              onOpenAtelier();
            }}
            className="px-8 py-4 rounded-full border border-[#d7a9a3]/40 bg-white/60 dark:bg-[#1a0f17]/60 backdrop-blur-md text-neutral-800 dark:text-[#f5ecea] font-medium text-sm sm:text-base tracking-wide hover:bg-[#d7a9a3]/10 transition-all duration-300 flex items-center gap-2.5 cursor-pointer hover:border-[#d7a9a3] shadow-sm"
          >
            <Sparkles className="w-4 h-4 text-[#d7a9a3]" />
            <span>{t.heroAtelierBtn}</span>
          </button>
        </motion.div>

        {/* Three Brand Profiles Quick Cards (secret_tashkent, greenmood_uz, secretberries_tashkent) */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-5 w-full max-w-5xl mb-5 text-left"
        >
          {/* Card 1: Secret Flowers */}
          <div
            onClick={() => {
              soundManager.playTick();
              onExploreCatalog('secret_flowers');
            }}
            className="group relative p-5 sm:p-6 rounded-2xl border border-rose-200/50 dark:border-rose-900/30 bg-white dark:bg-[#1a0f17] hover:border-rose-400/60 transition-all duration-300 cursor-pointer shadow-md hover:shadow-xl"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm uppercase tracking-widest text-rose-500 font-semibold flex items-center gap-1.5">
                <img src="/images/flowers/thumb/fl-05.jpg" alt="" className="w-7 h-7 rounded-full object-cover ring-1 ring-white/40" /> Secret Flowers
              </span>
              <a
                href="https://instagram.com/secret_tashkent"
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="text-neutral-400 hover:text-rose-500 transition-colors"
                title="Instagram @secret_tashkent"
              >
                <Instagram className="w-5 h-5" />
              </a>
            </div>
            <p className="text-sm text-neutral-600 dark:text-neutral-300 mb-3 line-clamp-2">
              {t.brandSecretDesc}
            </p>
            <div className="flex items-center justify-between text-xs sm:text-sm tabular-nums text-neutral-500 dark:text-neutral-400 border-t border-neutral-100 dark:border-neutral-800 pt-2">
              <span className="text-rose-500/90 font-medium">@secret_tashkent</span>
              <span className="group-hover:translate-x-0.5 transition-transform text-rose-400">→</span>
            </div>
          </div>

          {/* Card 2: Green Mood */}
          <div
            onClick={() => {
              soundManager.playTick();
              onExploreCatalog('green_mood');
            }}
            className="group relative p-5 sm:p-6 rounded-2xl border border-emerald-200/50 dark:border-emerald-900/30 bg-white dark:bg-[#1a0f17] hover:border-emerald-400/60 transition-all duration-300 cursor-pointer shadow-md hover:shadow-xl"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm uppercase tracking-widest text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1.5">
                <img src="/images/plants/thumb/gm-04.jpg" alt="" className="w-7 h-7 rounded-full object-cover ring-1 ring-white/40" /> Green Mood
              </span>
              <a
                href="https://instagram.com/greenmood_uz"
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="text-neutral-400 hover:text-emerald-500 transition-colors"
                title="Instagram @greenmood_uz"
              >
                <Instagram className="w-5 h-5" />
              </a>
            </div>
            <p className="text-sm text-neutral-600 dark:text-neutral-300 mb-3 line-clamp-2">
              {t.brandGreenMoodDesc}
            </p>
            <div className="flex items-center justify-between text-xs sm:text-sm tabular-nums text-neutral-500 dark:text-neutral-400 border-t border-neutral-100 dark:border-neutral-800 pt-2">
              <span className="text-emerald-600 dark:text-emerald-400 font-medium">@greenmood_uz</span>
              <span className="group-hover:translate-x-0.5 transition-transform text-emerald-500">→</span>
            </div>
          </div>

          {/* Card 3: Secret Berries */}
          <div
            onClick={() => {
              soundManager.playTick();
              onExploreCatalog('secret_berries');
            }}
            className="group relative p-5 sm:p-6 rounded-2xl border border-amber-200/50 dark:border-amber-900/30 bg-white dark:bg-[#1a0f17] hover:border-amber-400/60 transition-all duration-300 cursor-pointer shadow-md hover:shadow-xl"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm uppercase tracking-widest text-amber-600 dark:text-amber-400 font-semibold flex items-center gap-1.5">
                <img src="/images/berries/thumb/sb-03.jpg" alt="" className="w-7 h-7 rounded-full object-cover ring-1 ring-white/40" /> Secret Berries
              </span>
              <a
                href="https://instagram.com/secretberries_tashkent"
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="text-neutral-400 hover:text-amber-500 transition-colors"
                title="Instagram @secretberries_tashkent"
              >
                <Instagram className="w-5 h-5" />
              </a>
            </div>
            <p className="text-sm text-neutral-600 dark:text-neutral-300 mb-3 line-clamp-2">
              {t.brandBerriesDesc}
            </p>
            <div className="flex items-center justify-between text-xs sm:text-sm tabular-nums text-neutral-500 dark:text-neutral-400 border-t border-neutral-100 dark:border-neutral-800 pt-2">
              <span className="text-amber-600 dark:text-amber-400 font-medium">@secretberries_tashkent</span>
              <span className="group-hover:translate-x-0.5 transition-transform text-amber-500">→</span>
            </div>
          </div>
        </motion.div>

        {/* 4 Pillars Trust Bar */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5 max-w-5xl w-full text-sm sm:text-base text-neutral-700 dark:text-neutral-200 font-semibold">
          <div className="flex flex-col items-center justify-center text-center gap-3 py-5 sm:py-6 px-3 rounded-2xl bg-white dark:bg-[#1a0f17] border border-[#d7a9a3]/25 shadow-lg">
            <span className="w-12 h-12 sm:w-14 sm:h-14 rounded-2xl bg-[#d7a9a3]/12 flex items-center justify-center"><Clock className="w-6 h-6 sm:w-7 sm:h-7 text-amber-500" /></span>
            <span className="leading-snug">{t.heroFeatureExpress}</span>
          </div>
          <div className="flex flex-col items-center justify-center text-center gap-3 py-5 sm:py-6 px-3 rounded-2xl bg-white dark:bg-[#1a0f17] border border-[#d7a9a3]/25 shadow-lg">
            <span className="w-12 h-12 sm:w-14 sm:h-14 rounded-2xl bg-[#d7a9a3]/12 flex items-center justify-center"><Camera className="w-6 h-6 sm:w-7 sm:h-7 text-rose-500" /></span>
            <span className="leading-snug">{t.heroFeaturePhoto}</span>
          </div>
          <div className="flex flex-col items-center justify-center text-center gap-3 py-5 sm:py-6 px-3 rounded-2xl bg-white dark:bg-[#1a0f17] border border-[#d7a9a3]/25 shadow-lg">
            <span className="w-12 h-12 sm:w-14 sm:h-14 rounded-2xl bg-[#d7a9a3]/12 flex items-center justify-center"><CreditCard className="w-6 h-6 sm:w-7 sm:h-7 text-emerald-500" /></span>
            <span className="leading-snug">{t.heroFeaturePayment}</span>
          </div>
          <div className="flex flex-col items-center justify-center text-center gap-3 py-5 sm:py-6 px-3 rounded-2xl bg-white dark:bg-[#1a0f17] border border-[#d7a9a3]/25 shadow-lg">
            <span className="w-12 h-12 sm:w-14 sm:h-14 rounded-2xl bg-[#d7a9a3]/12 flex items-center justify-center"><ShieldCheck className="w-6 h-6 sm:w-7 sm:h-7 text-amber-400" /></span>
            <span className="leading-snug">{t.heroFeatureFresh}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
