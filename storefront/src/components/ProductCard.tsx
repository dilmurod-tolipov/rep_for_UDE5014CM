import React, { useState } from 'react';
import { motion } from 'motion/react';
import { Star, Clock, ShoppingBag, Eye, Sparkles } from 'lucide-react';
import { Product, Language } from '../types';
import { TRANSLATIONS } from '../translations';
import { soundManager } from '../utils/audio';

interface ProductCardProps {
  product: Product;
  lang: Language;
  onAddToCart: (product: Product) => void;
  onQuickView: (product: Product) => void;
}

import { SafeImage, thumbOf } from './SafeImage';

// Tilt and hover effects only on devices with a real mouse
export const SOLD_OUT = {"uz": "Sotuvda yo‘q", "ru": "Нет в наличии", "en": "Sold out"} as const;

const canHover = typeof window !== 'undefined' && window.matchMedia?.('(hover: hover) and (pointer: fine)').matches;

export function ProductCard({ product, lang, onAddToCart, onQuickView }: ProductCardProps) {
  const t = TRANSLATIONS[lang];
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const formatPrice = (amount: number) => {
    return amount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    setTilt({ x: x * 14, y: y * -14 });
  };

  const handleMouseLeave = () => {
    setTilt({ x: 0, y: 0 });
    setIsHovered(false);
  };


  return (
    <div
      onMouseMove={canHover ? handleMouseMove : undefined}
      onMouseEnter={() => {
        if (!canHover) return;
        setIsHovered(true);
        soundManager.playTick();
      }}
      onMouseLeave={handleMouseLeave}
      className="perspective-1000 h-full"
    >
      <motion.div
        style={{
          transform: isHovered
            ? `rotateX(${tilt.y}deg) rotateY(${tilt.x}deg) scale3d(1.02, 1.02, 1.02)`
            : 'rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)',
          transition: 'transform 0.15s ease-out'
        }}
        className="group relative h-full rounded-2xl overflow-hidden border border-neutral-200/80 dark:border-neutral-800 bg-white dark:bg-neutral-900/90 shadow-md hover:shadow-2xl transition-shadow duration-300 flex flex-col justify-between"
      >
        {/* Specular shine layer */}
        <div
          className="pointer-events-none absolute inset-0 z-20 transition-opacity duration-300 opacity-0 group-hover:opacity-100 bg-gradient-to-tr from-white/0 via-white/10 to-amber-200/10 mix-blend-overlay"
        />

        {/* Media Container (tapping the photo opens the product on touch screens) */}
        <div
          className="relative aspect-[4/5] w-full overflow-hidden bg-neutral-100 dark:bg-neutral-800 cursor-pointer"
          onClick={() => onQuickView(product)}
        >
          <SafeImage
            src={thumbOf(product.images[0])}
            alt={product.title[lang]}
            loading="lazy"
            decoding="async"
            className="w-full h-full object-cover object-center group-hover:scale-108 transition-transform duration-700 ease-out"
          />

          {/* Badges */}
          <div className="absolute top-3 left-3 flex flex-col gap-1.5 z-10">
            {product.inStock === false && (
              <span className="px-2.5 py-1 rounded-full text-xs uppercase font-bold tracking-wider bg-neutral-900/85 text-white shadow-md">
                {SOLD_OUT[lang]}
              </span>
            )}
            {product.isBestseller && (
              <span className="px-2.5 py-1 rounded-full text-xs uppercase font-bold tracking-wider bg-[#291823] text-[#d7a9a3] border border-[#d7a9a3]/50 flex items-center gap-1 shadow-md">
                <Sparkles className="w-3 h-3 text-[#d7a9a3]" />
                {t.bestsellerBadge}
              </span>
            )}
            {product.isNew && (
              <span className="px-2.5 py-1 rounded-full text-xs uppercase font-bold tracking-wider bg-[#d7a9a3] text-[#291823] shadow-md">
                {t.newBadge}
              </span>
            )}
          </div>

          {/* Quick View Hover Button */}
          <div className="absolute inset-0 bg-black/35 opacity-0 [@media(hover:hover)]:group-hover:opacity-100 pointer-events-none [@media(hover:hover)]:group-hover:pointer-events-auto transition-opacity duration-300 flex items-center justify-center gap-2 p-4 z-10">
            <button
              id={`btn-quick-view-${product.id}`}
              onClick={(e) => {
                e.stopPropagation();
                soundManager.playChime(750);
                onQuickView(product);
              }}
              className="px-4 py-2.5 rounded-full bg-white/95 dark:bg-[#1a0f17]/95 text-[#291823] dark:text-[#f5ecea] border border-[#d7a9a3]/40 text-xs font-semibold tracking-wide hover:border-[#d7a9a3] shadow-xl backdrop-blur-md transition-all flex items-center gap-1.5 cursor-pointer transform translate-y-2 group-hover:translate-y-0 duration-300"
            >
              <Eye className="w-3.5 h-3.5 text-[#d7a9a3]" />
              <span>{t.detailsTabDesc}</span>
            </button>
          </div>

          {/* Prep time badge bottom overlay */}
          <div className="absolute bottom-2 left-2 z-10 px-2.5 py-1 rounded-lg bg-[#1a0f17]/70 backdrop-blur-md text-xs text-[#f5ecea] flex items-center gap-1 tabular-nums border border-[#d7a9a3]/20">
            <Clock className="w-3 h-3 text-[#d7a9a3]" />
            <span>{product.prepTimeMinutes} min</span>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 sm:p-5 flex-1 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs text-neutral-500 dark:text-neutral-400 mb-1.5">
              <span className="uppercase tracking-widest text-xs font-semibold text-[#b88680] dark:text-[#d7a9a3]">
                {product.brand === 'secret_flowers' ? 'Secret Flowers' : product.brand === 'green_mood' ? 'Green Mood' : 'Secret Berries'}
              </span>
              {product.reviewsCount > 0 && <div className="flex items-center gap-1">
                <Star className="w-3 h-3 text-[#d7a9a3] fill-[#d7a9a3]" />
                <span className="font-semibold text-neutral-700 dark:text-neutral-300">{product.rating}</span>
                <span className="text-xs opacity-70">({product.reviewsCount})</span>
              </div>}
            </div>

            <h3
              onClick={() => onQuickView(product)}
              className="font-serif text-base sm:text-lg font-medium text-neutral-900 dark:text-neutral-100 hover:text-[#d7a9a3] transition-colors cursor-pointer line-clamp-1"
            >
              {product.title[lang]}
            </h3>

            <p className="text-xs text-neutral-500 dark:text-neutral-400 line-clamp-2 mt-1 font-light">
              {product.subtitle[lang]}
            </p>
          </div>

          {/* Pricing and Action */}
          <div className="pt-4 mt-3 border-t border-neutral-100 dark:border-neutral-800 flex items-center justify-between">
            <div>
              <div className="font-serif text-base sm:text-lg font-semibold text-neutral-900 dark:text-white">
                {formatPrice(product.price)} <span className="text-xs font-sans font-normal text-neutral-500">{t.uzs}</span>
              </div>
              {product.oldPrice && (
                <div className="text-xs text-neutral-400 line-through">
                  {formatPrice(product.oldPrice)} {t.uzs}
                </div>
              )}
            </div>

            <button
              id={`btn-add-cart-${product.id}`}
              disabled={product.inStock === false}
              onClick={(e) => {
                e.stopPropagation();
                soundManager.playPluck();
                onAddToCart(product);
              }}
              className="p-2.5 rounded-full bg-[#291823] text-[#d7a9a3] hover:bg-[#3d2034] dark:bg-[#d7a9a3] dark:text-[#291823] dark:hover:bg-[#e2bbb6] border border-[#d7a9a3]/40 transition-transform active:scale-95 shadow-md flex items-center justify-center cursor-pointer disabled:opacity-35 disabled:cursor-not-allowed"
              title={t.addToCart}
              aria-label={t.addToCart}
            >
              <ShoppingBag className="w-4 h-4" />
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
