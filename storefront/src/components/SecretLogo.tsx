import React, { useState } from 'react';

interface SecretLogoProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  className?: string;
  showText?: boolean;
}

const SIZES = {
  xs: 'w-7 h-7',
  sm: 'w-9 h-9 sm:w-10 sm:h-10',
  md: 'w-12 h-12 sm:w-14 sm:h-14',
  lg: 'w-16 h-16 sm:w-20 sm:h-20',
  xl: 'w-24 h-24 sm:w-28 sm:h-28',
  '2xl': 'w-32 h-32 sm:w-36 sm:h-36'
};

export function SecretLogo({ size = 'sm', className = '', showText = false }: SecretLogoProps) {
  const [imageError, setImageError] = useState(false);
  const sizeClass = SIZES[size] || SIZES.sm;

  return (
    <div className={`inline-flex items-center gap-3 ${className}`}>
      <div
        className={`relative rounded-full overflow-hidden shadow-md shrink-0 border border-[#4a2e3f]/40 hover:border-amber-400/50 transition-all duration-300 ${sizeClass} bg-[#291823]`}
      >
        {!imageError ? (
          <img
            src="/logo-circle.webp"
            alt="Secret Flowers and More"
            className="w-full h-full object-cover object-center rounded-full select-none"
            referrerPolicy="no-referrer"
            onError={() => setImageError(true)}
          />
        ) : (
          /* High-Fidelity Vector SVG Fallback strictly reproducing the uploaded emblem */
          <svg
            viewBox="0 0 400 400"
            className="w-full h-full"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* Dark Plum Aubergine Circle */}
            <circle cx="200" cy="200" r="200" fill="#291823" />
            
            {/* Delicate Arch with Key-Flower Motif */}
            <rect
              x="165"
              y="45"
              width="70"
              height="115"
              rx="35"
              stroke="#d7a9a3"
              strokeWidth="3.5"
              fill="none"
            />
            
            {/* Stylized Lotus/Tulip inside Arch */}
            <path
              d="M200 68 C192 82 188 98 200 114 C212 98 208 82 200 68 Z"
              stroke="#d7a9a3"
              strokeWidth="3"
              fill="none"
            />
            <path
              d="M185 86 C180 96 182 108 200 114"
              stroke="#d7a9a3"
              strokeWidth="2.5"
              fill="none"
            />
            <path
              d="M215 86 C220 96 218 108 200 114"
              stroke="#d7a9a3"
              strokeWidth="2.5"
              fill="none"
            />
            
            {/* Key Stem & Bit */}
            <line x1="200" y1="114" x2="200" y2="168" stroke="#d7a9a3" strokeWidth="3.5" />
            <line x1="200" y1="148" x2="212" y2="148" stroke="#d7a9a3" strokeWidth="3" />
            <line x1="200" y1="158" x2="210" y2="158" stroke="#d7a9a3" strokeWidth="3" />
            
            {/* Elegant Serif SECRET */}
            <text
              x="200"
              y="250"
              textAnchor="middle"
              fill="#d7a9a3"
              fontFamily="'Cinzel', 'Playfair Display', Georgia, serif"
              fontSize="64"
              letterSpacing="7"
              fontWeight="400"
            >
              SECRET
            </text>
            
            {/* FLOWERS AND MORE */}
            <text
              x="200"
              y="288"
              textAnchor="middle"
              fill="#c89f9a"
              fontFamily="'Plus Jakarta Sans', system-ui, sans-serif"
              fontSize="16"
              letterSpacing="11"
              fontWeight="300"
            >
              FLOWERS AND MORE
            </text>
          </svg>
        )}
      </div>

      {showText && (
        <div className="flex flex-col text-left">
          <span className="font-display tracking-[0.25em] text-lg sm:text-xl font-bold text-neutral-900 dark:text-white leading-tight">
            SECRET
          </span>
          <span className="text-[9px] sm:text-[10px] uppercase tracking-[0.25em] text-neutral-500 dark:text-neutral-400 font-sans -mt-0.5">
            FLOWERS AND MORE
          </span>
        </div>
      )}
    </div>
  );
}
