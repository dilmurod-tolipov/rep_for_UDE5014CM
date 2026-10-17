import { useState } from 'react';
import { motion } from 'motion/react';
import { Sparkles, Check, ShoppingBag, Palette, Layers, Award, Feather } from 'lucide-react';
import { Language, CustomBouquetConfig, Product } from '../types';
import { TRANSLATIONS } from '../translations';
import { soundManager } from '../utils/audio';

interface BouquetBuilderProps {
  lang: Language;
  onAddCustomBouquet: (customProduct: Product, cardMessage: string) => void;
}

import { SafeImage } from './SafeImage';

export function BouquetBuilder({ lang, onAddCustomBouquet }: BouquetBuilderProps) {
  const t = TRANSLATIONS[lang];

  const [config, setConfig] = useState<CustomBouquetConfig>({
    boxType: 'cream_hatbox',
    focalFlower: 'peonies',
    flowerColor: 'blush',
    flowerQuantity: 25,
    foliage: 'eucalyptus',
    ribbonColor: 'champagne',
    waxSealMonogram: 'S',
    cardText: ''
  });

  const boxes = [
    { id: 'cream_hatbox', label: { uz: 'Krem rangli shlyapa qutisi', ru: 'Шляпная коробка крем', en: 'Cream velvet hatbox' }, price: 180000, img: 'https://images.unsplash.com/photo-1561181286-d3fee7d55364?auto=format&fit=crop&w=400&q=80' },
    { id: 'velvet_black', label: { uz: 'Qora baxmal silindr', ru: 'Чёрный бархатный цилиндр', en: 'Black velvet cylinder' }, price: 220000, img: 'https://images.unsplash.com/photo-1548094891-c4969f91e649?auto=format&fit=crop&w=400&q=80' },
    { id: 'kraft_wrap', label: { uz: 'Dizaynerlik qog‘ozi', ru: 'Дизайнерская бумага', en: 'Designer layered paper' }, price: 90000, img: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=400&q=80' },
    { id: 'crystal_vase', label: { uz: 'Kristall vaza', ru: 'Хрустальная ваза', en: 'Crystal glass vase' }, price: 250000, img: 'https://images.unsplash.com/photo-1581783342308-f792dbdd27c5?auto=format&fit=crop&w=400&q=80' }
  ];

  const flowers = [
    { id: 'peonies', label: { uz: 'Gollandiya pionlari', ru: 'Голландские пионы', en: 'Dutch peonies' }, stemPrice: 55000, icon: '🌸' },
    { id: 'ecuador_roses', label: { uz: 'Ekvador atirgullari', ru: 'Эквадорские розы', en: 'Ecuadorian roses' }, stemPrice: 32000, icon: '🌹' },
    { id: 'hydrangeas', label: { uz: 'Gollandiya gortenziyalari', ru: 'Голландские гортензии', en: 'Dutch hydrangeas' }, stemPrice: 95000, icon: '💮' },
    { id: 'lisianthus', label: { uz: 'Liziantuslar', ru: 'Эустома', en: 'Lisianthus' }, stemPrice: 28000, icon: '🌺' }
  ];

  const colors = [
    { id: 'blush', name: { uz: 'Pushti', ru: 'Пудровый', en: 'Blush' }, bg: 'bg-rose-200' },
    { id: 'crimson', name: { uz: 'Qizil', ru: 'Алый', en: 'Crimson' }, bg: 'bg-rose-800' },
    { id: 'pure_white', name: { uz: 'Oq', ru: 'Белый', en: 'White' }, bg: 'bg-stone-100' },
    { id: 'pastel_blue', name: { uz: 'Havorang', ru: 'Голубой', en: 'Sky blue' }, bg: 'bg-sky-200' },
    { id: 'lavender', name: { uz: 'Lavanda', ru: 'Лавандовый', en: 'Lavender' }, bg: 'bg-purple-200' }
  ];

  const quantities = [15, 25, 51, 101];

  const foliageOptions = [
    { id: 'eucalyptus', label: { uz: 'Kumushrang evkalipt', ru: 'Серебристый эвкалипт', en: 'Silver eucalyptus' }, price: 70000 },
    { id: 'babys_breath', label: { uz: 'Oq gipsofila', ru: 'Белая гипсофила', en: 'Baby’s breath' }, price: 60000 },
    { id: 'none', label: { uz: 'Yashilliksiz (monobuket)', ru: 'Без зелени (монобукет)', en: 'No foliage (mono)' }, price: 0 }
  ];

  const ribbons = [
    { id: 'champagne', label: { uz: 'Shampan', ru: 'Шампань', en: 'Champagne' }, color: 'bg-amber-100' },
    { id: 'burgundy', label: { uz: 'Bordo', ru: 'Бордо', en: 'Burgundy' }, color: 'bg-rose-900' },
    { id: 'emerald', label: { uz: 'Zumrad', ru: 'Изумрудный', en: 'Emerald' }, color: 'bg-emerald-900' },
    { id: 'rose_gold', label: { uz: 'Pushti oltin', ru: 'Розовое золото', en: 'Rose gold' }, color: 'bg-rose-300' }
  ];

  // Price Calculation
  const selectedBox = boxes.find((b) => b.id === config.boxType) || boxes[0];
  const selectedFlower = flowers.find((f) => f.id === config.focalFlower) || flowers[0];
  const selectedFoliage = foliageOptions.find((fo) => fo.id === config.foliage) || foliageOptions[0];

  const flowerTotal = selectedFlower.stemPrice * (selectedFlower.id === 'hydrangeas' ? Math.min(config.flowerQuantity, 9) : config.flowerQuantity);
  const calculatedPrice = selectedBox.price + flowerTotal + selectedFoliage.price + 50000; // includes bespoke crafting fee

  const formatPrice = (amount: number) => {
    return amount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  };

  const handleCreateAndAdd = () => {
    soundManager.playSuccessChord();

    const customProduct: Product = {
      id: `custom-${Date.now()}`,
      brand: 'secret_flowers',
      category: 'custom_atelier',
      tags: ['bespoke', 'atelier', 'custom'],
      isNew: true,
      rating: 5.0,
      reviewsCount: 1,
      price: calculatedPrice,
      prepTimeMinutes: 60,
      dimensions: '50cm × 55cm (Bespoke)',
      images: [selectedBox.img],
      title: {
        uz: `Secret Atelier: ${selectedFlower.label.uz} (${config.flowerQuantity} dona)`,
        ru: `Secret Atelier: ${selectedFlower.label.ru} (${config.flowerQuantity} шт)`,
        en: `Secret Atelier: ${selectedFlower.label.en} (${config.flowerQuantity} stems)`
      },
      subtitle: {
        uz: `${selectedBox.label.uz}, ${selectedFoliage.label.uz}`,
        ru: `${selectedBox.label.ru}, ${selectedFoliage.label.ru}`,
        en: `${selectedBox.label.en}, ${selectedFoliage.label.en}`
      },
      description: {
        uz: `Mijoz tomonidan Secret Atelier konstruktorida yig‘ilgan shaxsiy mualliflik guldastasi.`,
        ru: `Индивидуальная композиция, собранная заказчиком в онлайн-конструкторе Secret Atelier.`,
        en: `Bespoke artisanal floral arrangement assembled via Secret Atelier.`
      },
      composition: {
        uz: [`${config.flowerQuantity} dona ${selectedFlower.label.uz}`, selectedBox.label.uz, selectedFoliage.label.uz, `Muhr: ${config.waxSealMonogram}`],
        ru: [`${config.flowerQuantity} шт ${selectedFlower.label.ru}`, selectedBox.label.ru, selectedFoliage.label.ru, `Печать: ${config.waxSealMonogram}`],
        en: [`${config.flowerQuantity} stems ${selectedFlower.label.en}`, selectedBox.label.en, selectedFoliage.label.en, `Seal: ${config.waxSealMonogram}`]
      },
      careTips: {
        uz: ['Har kuni 150ml sovuq toza suv bering', 'Salqin xonada saqlang'],
        ru: ['Ежедневно подливать 150 мл холодной воды', 'Хранить в прохладе'],
        en: ['Add 150ml cold water daily', 'Store in a cool room']
      }
    };

    onAddCustomBouquet(customProduct, config.cardText);
  };

  return (
    <section id="section-atelier" className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto relative z-10">
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto mb-14">
        <div className="inline-flex items-center gap-2.5 px-6 py-2.5 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-300 text-sm sm:text-base font-semibold uppercase tracking-widest mb-4 border border-amber-500/30">
          <Sparkles className="w-5 h-5 text-amber-500" />
          <span>{t.studioBadge}</span>
        </div>
        <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-light text-neutral-900 dark:text-white mb-3">
          {t.atelierTitle}
        </h2>
        <p className="text-neutral-600 dark:text-neutral-400 text-sm sm:text-base font-light">
          {t.atelierSubtitle}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: Interactive Controls (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Step 1: Vessel */}
          <div className="p-6 rounded-3xl border border-neutral-200 dark:border-neutral-800 bg-white/70 dark:bg-neutral-900/70 backdrop-blur-md shadow-sm">
            <h3 className="text-sm sm:text-base uppercase font-bold tracking-wider text-amber-600 dark:text-amber-400 mb-4 flex items-center gap-2">
              <Layers className="w-5 h-5" />
              <span>{t.step1Box}</span>
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {boxes.map((b) => (
                <button
                  key={b.id}
                  onClick={() => {
                    soundManager.playTick();
                    setConfig({ ...config, boxType: b.id as any });
                  }}
                  className={`p-4 rounded-2xl border text-left flex flex-col justify-between transition-all cursor-pointer ${
                    config.boxType === b.id
                      ? 'border-amber-500 bg-amber-50/50 dark:bg-amber-950/40 shadow-md ring-1 ring-amber-500'
                      : 'border-neutral-200 dark:border-neutral-800 hover:border-neutral-300'
                  }`}
                >
                  <SafeImage key={b.img} src={b.img} alt={b.label[lang]} loading="lazy" className="w-full h-24 sm:h-28 object-cover rounded-xl mb-3" />
                  <p className="text-sm font-medium text-neutral-800 dark:text-neutral-200 line-clamp-2 leading-tight">
                    {b.label[lang]}
                  </p>
                  <p className="text-xs text-amber-600 dark:text-amber-400 tabular-nums mt-1">
                    +{formatPrice(b.price)} {t.uzs}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Step 2: Focal Flower */}
          <div className="p-6 rounded-3xl border border-neutral-200 dark:border-neutral-800 bg-white/70 dark:bg-neutral-900/70 backdrop-blur-md shadow-sm">
            <h3 className="text-sm sm:text-base uppercase font-bold tracking-wider text-rose-500 mb-4 flex items-center gap-2">
              <Feather className="w-5 h-5" />
              <span>{t.step2Flower}</span>
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {flowers.map((f) => (
                <button
                  key={f.id}
                  onClick={() => {
                    soundManager.playTick();
                    setConfig({ ...config, focalFlower: f.id as any });
                  }}
                  className={`p-5 rounded-2xl border text-center transition-all cursor-pointer ${
                    config.focalFlower === f.id
                      ? 'border-rose-500 bg-rose-50/50 dark:bg-rose-950/40 shadow-md ring-1 ring-rose-500'
                      : 'border-neutral-200 dark:border-neutral-800 hover:border-neutral-300'
                  }`}
                >
                  <span className="text-4xl mb-2 block">{f.icon}</span>
                  <p className="text-sm font-medium text-neutral-800 dark:text-neutral-200 line-clamp-2 leading-tight">
                    {f.label[lang]}
                  </p>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400 tabular-nums mt-1">
                    {formatPrice(f.stemPrice)} {t.uzs} · {t.perStem}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Step 3: Color & Quantity */}
          <div className="p-6 rounded-3xl border border-neutral-200 dark:border-neutral-800 bg-white/70 dark:bg-neutral-900/70 backdrop-blur-md shadow-sm">
            <h3 className="text-sm sm:text-base uppercase font-bold tracking-wider text-emerald-600 dark:text-emerald-400 mb-4 flex items-center gap-2">
              <Palette className="w-5 h-5" />
              <span>{t.step3Color}</span>
            </h3>

            {/* Colors */}
            <div className="flex flex-wrap items-center gap-3 mb-5">
              {colors.map((c) => (
                <button
                  key={c.id}
                  onClick={() => {
                    soundManager.playTick();
                    setConfig({ ...config, flowerColor: c.id as any });
                  }}
                  className={`flex items-center gap-2.5 px-4 min-h-[44px] rounded-full border text-sm cursor-pointer transition-all ${
                    config.flowerColor === c.id
                      ? 'border-neutral-900 dark:border-white font-semibold shadow-sm'
                      : 'border-neutral-200 dark:border-neutral-700 opacity-70 hover:opacity-100'
                  }`}
                >
                  <span className={`w-5 h-5 rounded-full border border-black/20 ${c.bg}`} />
                  <span className="text-neutral-800 dark:text-neutral-200 text-sm">{c.name[lang]}</span>
                </button>
              ))}
            </div>

            {/* Stems count */}
            <div className="flex items-center gap-3">
              {quantities.map((qty) => (
                <button
                  key={qty}
                  onClick={() => {
                    soundManager.playTick();
                    setConfig({ ...config, flowerQuantity: qty });
                  }}
                  className={`flex-1 py-3.5 rounded-xl text-sm sm:text-base tabular-nums font-medium border cursor-pointer transition-all ${
                    config.flowerQuantity === qty
                      ? 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-950 border-neutral-900 dark:border-white shadow-md'
                      : 'border-neutral-200 dark:border-neutral-800 text-neutral-700 dark:text-neutral-300 hover:border-neutral-400'
                  }`}
                >
                  {qty} {t.stems}
                </button>
              ))}
            </div>
          </div>

          {/* Step 4 & 5: Foliage, Ribbon & Wax Seal */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Foliage */}
            <div className="p-5 rounded-3xl border border-neutral-200 dark:border-neutral-800 bg-white/70 dark:bg-neutral-900/70 backdrop-blur-md">
              <h4 className="text-sm font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400 mb-4">{t.step4Foliage}</h4>
              <div className="space-y-2">
                {foliageOptions.map((fo) => (
                  <div
                    key={fo.id}
                    onClick={() => {
                      soundManager.playTick();
                      setConfig({ ...config, foliage: fo.id as any });
                    }}
                    className={`p-3.5 min-h-[48px] rounded-xl border text-sm flex items-center justify-between cursor-pointer transition-colors ${
                      config.foliage === fo.id ? 'border-amber-500 bg-amber-50/40 dark:bg-amber-950/30' : 'border-neutral-200 dark:border-neutral-800'
                    }`}
                  >
                    <span className="text-neutral-800 dark:text-neutral-200 text-sm">{fo.label[lang]}</span>
                    {config.foliage === fo.id && <Check className="w-3.5 h-3.5 text-amber-500" />}
                  </div>
                ))}
              </div>
            </div>

            {/* Monogram Seal */}
            <div className="p-5 rounded-3xl border border-neutral-200 dark:border-neutral-800 bg-white/70 dark:bg-neutral-900/70 backdrop-blur-md">
              <h4 className="text-sm font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400 mb-4">{t.step5Ribbon}</h4>
              <div className="flex items-center gap-2 mb-3">
                {ribbons.map((r) => (
                  <button
                    key={r.id}
                    onClick={() => {
                      soundManager.playTick();
                      setConfig({ ...config, ribbonColor: r.id as any });
                    }}
                    className={`w-11 h-11 rounded-full border-2 ${r.color} cursor-pointer transition-transform ${
                      config.ribbonColor === r.id ? 'scale-110 ring-2 ring-amber-500' : 'opacity-60'
                    }`}
                    title={r.label[lang]}
                    aria-label={r.label[lang]}
                  />
                ))}
              </div>

              <div className="flex items-center gap-2 text-xs text-neutral-600 dark:text-neutral-300">
                <Award className="w-5 h-5 text-amber-500" />
                <span className="text-sm">{t.monogramLabel}: <strong>{t.monogramValue}</strong></span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Live 3D Preview & Cart Action (5 cols) */}
        <div className="lg:col-span-5 sticky top-24">
          <motion.div
            layout
            className="p-6 sm:p-8 rounded-3xl border border-amber-500/30 bg-gradient-to-b from-white to-amber-50/20 dark:from-neutral-900 dark:to-neutral-950 shadow-xl"
          >
            <div className="flex items-center justify-between text-sm tabular-nums uppercase tracking-widest text-amber-600 dark:text-amber-400 mb-5">
              <span>{t.atelierMaison}</span>
              <span className="px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20">{t.preview3d}</span>
            </div>

            {/* Simulated 3D Vessel View */}
            <div className="relative aspect-[4/3] w-full rounded-2xl overflow-hidden border border-neutral-200 dark:border-neutral-800 mb-6 shadow-inner bg-neutral-100 dark:bg-neutral-800">
              <SafeImage
                key={selectedBox.img}
                src={selectedBox.img}
                alt={selectedBox.label[lang]}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-black/20" />

              {/* Live Spec Badges */}
              <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-white text-xs">
                <span className="font-serif text-2xl tracking-wide flex items-center gap-2">
                  <span>{selectedFlower.icon}</span>
                  <span className="tabular-nums">{config.flowerQuantity} {t.stems}</span>
                </span>
                <span className="px-2.5 py-1 rounded-full bg-amber-500/90 text-neutral-950 font-bold text-xs uppercase tabular-nums">
                  {t.waxSealBadge}
                </span>
              </div>
            </div>

            {/* Summary Recipe List */}
            <div className="space-y-3 mb-6 text-sm sm:text-base text-neutral-600 dark:text-neutral-300 font-light border-y border-neutral-200 dark:border-neutral-800 py-4">
              <div className="flex justify-between">
                <span>{selectedBox.label[lang]}</span>
                <span className="tabular-nums text-neutral-900 dark:text-white">+{formatPrice(selectedBox.price)} {t.uzs}</span>
              </div>
              <div className="flex justify-between">
                <span>{selectedFlower.label[lang]} × {config.flowerQuantity}</span>
                <span className="tabular-nums text-neutral-900 dark:text-white">+{formatPrice(flowerTotal)} {t.uzs}</span>
              </div>
              <div className="flex justify-between">
                <span>{selectedFoliage.label[lang]}</span>
                <span className="tabular-nums text-neutral-900 dark:text-white">+{formatPrice(selectedFoliage.price)} {t.uzs}</span>
              </div>
            </div>

            {/* Total Price */}
            <div className="flex items-baseline justify-between mb-6">
              <span className="text-sm uppercase tracking-widest text-neutral-500 font-semibold">{t.atelierEstimatedPrice}</span>
              <span className="font-serif text-4xl sm:text-5xl font-semibold text-neutral-900 dark:text-[#d7a9a3]">
                {formatPrice(calculatedPrice)} <span className="text-xs font-sans font-normal text-neutral-500">{t.uzs}</span>
              </span>
            </div>

            {/* Add to Cart CTA */}
            <button
              id="btn-add-custom-bouquet"
              onClick={handleCreateAndAdd}
              className="w-full py-5 rounded-full bg-[#291823] text-[#d7a9a3] dark:bg-[#d7a9a3] dark:text-[#291823] font-semibold text-base sm:text-lg tracking-wide shadow-xl hover:scale-[1.01] transition-transform active:scale-98 flex items-center justify-center gap-2.5 cursor-pointer border border-[#d7a9a3]/40"
            >
              <ShoppingBag className="w-5 h-5" />
              <span>{t.createCustomBouquetBtn}</span>
            </button>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
