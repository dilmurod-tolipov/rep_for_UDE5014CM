import { motion } from 'motion/react';
import { Instagram, ArrowUpRight, Sparkles, Heart } from 'lucide-react';
import { Language, BrandCategory } from '../types';
import { TRANSLATIONS } from '../translations';
import { soundManager } from '../utils/audio';

interface BrandShowcaseProps {
  lang: Language;
  onSelectBrand: (brand: BrandCategory) => void;
}

export function BrandShowcase({ lang, onSelectBrand }: BrandShowcaseProps) {
  const t = TRANSLATIONS[lang];

  const brands = [
    {
      id: 'secret_flowers' as BrandCategory,
      name: t.brandSecretTitle,
      handle: '@secret_tashkent',
      instagramUrl: 'https://instagram.com/secret_tashkent',
      description: t.brandSecretDesc,
      tag: 'Haute Floristique',
      accentColor: 'from-[#d7a9a3]/20 to-[#291823]/20',
      borderColor: 'hover:border-[#d7a9a3]',
      badgeColor: 'bg-[#d7a9a3]/15 text-[#291823] dark:text-[#f5ecea] border-[#d7a9a3]/40',
      imageMain: '/images/flowers/thumb/fl-02.jpg',
      imageSecondary: '/images/flowers/thumb/fl-05.jpg',
      stats: '19.4K followers • Tashkent'
    },
    {
      id: 'green_mood' as BrandCategory,
      name: t.brandGreenMoodTitle,
      handle: '@greenmood_uz',
      instagramUrl: 'https://instagram.com/greenmood_uz',
      description: t.brandGreenMoodDesc,
      tag: 'Interior Landscaping',
      accentColor: 'from-emerald-500/20 to-teal-500/20',
      borderColor: 'hover:border-emerald-400/50',
      badgeColor: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-300/30',
      imageMain: '/images/plants/thumb/gm-04.jpg',
      imageSecondary: '/images/plants/thumb/gm-05.jpg',
      stats: '14.2K followers • Tashkent'
    },
    {
      id: 'secret_berries' as BrandCategory,
      name: t.brandBerriesTitle,
      handle: '@secretberries_tashkent',
      instagramUrl: 'https://instagram.com/secretberries_tashkent',
      description: t.brandBerriesDesc,
      tag: 'Belgian Confection',
      accentColor: 'from-amber-500/20 to-rose-600/20',
      borderColor: 'hover:border-amber-400/50',
      badgeColor: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-300/30',
      imageMain: '/images/berries/thumb/sb-03.jpg',
      imageSecondary: '/images/berries/thumb/sb-04.jpg',
      stats: '28.7K followers • Tashkent'
    }
  ];

  return (
    <section id="section-brands" className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto relative z-10">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#d7a9a3]/15 text-[#291823] dark:text-[#f5ecea] text-xs font-semibold uppercase tracking-widest mb-3 border border-[#d7a9a3]/40">
          <Sparkles className="w-3.5 h-3.5 text-[#d7a9a3]" />
          <span>{t.brandsKicker}</span>
        </div>
        <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-light text-neutral-900 dark:text-[#f8f5f0] mb-4">
          {t.brandSectionTitle}
        </h2>
        <p className="text-neutral-600 dark:text-neutral-400 text-sm sm:text-base font-light">
          {t.brandSectionSubtitle}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {brands.map((b, index) => (
          <motion.div
            key={b.id}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ duration: 0.6, delay: index * 0.15 }}
            className={`group relative rounded-3xl overflow-hidden border border-neutral-200 dark:border-neutral-800 bg-white/70 dark:bg-neutral-900/70 backdrop-blur-xl transition-all duration-500 ${b.borderColor} hover:shadow-2xl flex flex-col`}
          >
            {/* Image Showcase with 3D hover scale */}
            <div className="relative h-64 sm:h-72 w-full overflow-hidden bg-neutral-100 dark:bg-neutral-800">
              <img
                src={b.imageMain}
                alt={b.name}
                loading="lazy"
                referrerPolicy="no-referrer"
                className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-700 ease-out"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />

              {/* Tag & Secondary floating inset */}
              <div className="absolute top-4 left-4 right-4 flex items-center justify-between z-10">
                <span className={`px-3 py-1 rounded-full text-xs font-medium border backdrop-blur-md ${b.badgeColor}`}>
                  {b.tag}
                </span>
                <a
                  href={b.instagramUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="p-2 rounded-full bg-black/40 hover:bg-black/70 backdrop-blur-md text-white transition-colors flex items-center gap-1 text-xs"
                  title={`Open ${b.handle} on Instagram`}
                >
                  <Instagram className="w-3.5 h-3.5 text-pink-400" />
                  <span className="text-sm tabular-nums hidden sm:inline">{b.handle}</span>
                  <ArrowUpRight className="w-3 h-3 text-neutral-300" />
                </a>
              </div>

              {/* Floating secondary miniature preview */}
              <div className="absolute bottom-4 right-4 w-16 h-16 rounded-xl overflow-hidden border-2 border-white/50 shadow-lg hidden sm:block group-hover:scale-110 transition-transform">
                <img
                  src={b.imageSecondary}
                  alt="Detail"
                  loading="lazy"
                  referrerPolicy="no-referrer"
                  className="w-full h-full object-cover"
                />
              </div>

              <div className="absolute bottom-4 left-4 text-white">
                <h3 className="font-serif text-2xl font-light tracking-wide">{b.name}</h3>
                <p className="text-xs text-neutral-300 tabular-nums flex items-center gap-1 mt-0.5">
                  <Heart className="w-3 h-3 text-rose-400 fill-rose-400" />
                  <span>{b.stats}</span>
                </p>
              </div>
            </div>

            {/* Content & Action */}
            <div className="p-6 flex-1 flex flex-col justify-between">
              <p className="text-xs sm:text-sm text-neutral-600 dark:text-neutral-300 font-light leading-relaxed mb-6">
                {b.description}
              </p>

              <div className="pt-4 border-t border-neutral-100 dark:border-neutral-800 flex items-center justify-between">
                <button
                  id={`btn-explore-${b.id}`}
                  onClick={() => {
                    soundManager.playPluck();
                    onSelectBrand(b.id);
                  }}
                  className="text-xs font-semibold uppercase tracking-wider text-neutral-900 dark:text-neutral-100 group-hover:text-amber-500 transition-colors flex items-center gap-1 cursor-pointer"
                >
                  <span>{t.navCatalog}</span>
                  <span className="group-hover:translate-x-1 transition-transform">→</span>
                </button>

                <a
                  href={b.instagramUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-neutral-400 hover:text-pink-500 transition-colors flex items-center gap-1 tabular-nums"
                >
                  <Instagram className="w-3 h-3" />
                  <span>{t.viewOnInstagram}</span>
                </a>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
