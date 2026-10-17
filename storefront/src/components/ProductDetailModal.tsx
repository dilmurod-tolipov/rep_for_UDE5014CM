import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, Star, Clock, Check, ShoppingBag, Truck, ShieldCheck, Heart, Sparkles, Plus } from 'lucide-react';
import { Product, Language } from '../types';
import { TRANSLATIONS } from '../translations';
import { ADDONS_CATALOG } from '../data/products';
import { soundManager } from '../utils/audio';

interface ProductDetailModalProps {
  product: Product | null;
  isOpen: boolean;
  onClose: () => void;
  lang: Language;
  onAddToCart: (product: Product, quantity: number, cardNote: string, selectedAddOns: typeof ADDONS_CATALOG) => void;
}

import { SafeImage } from './SafeImage';
import { SOLD_OUT } from './ProductCard';

export function ProductDetailModal({ product, isOpen, onClose, lang, onAddToCart }: ProductDetailModalProps) {
  const t = TRANSLATIONS[lang];
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [activeTab, setActiveTab] = useState<'desc' | 'comp' | 'care' | 'delivery'>('desc');
  const [quantity, setQuantity] = useState(1);
  const [cardMessage, setCardMessage] = useState('');
  const [selectedAddOnIds, setSelectedAddOnIds] = useState<string[]>([]);
  const [showAddedAlert, setShowAddedAlert] = useState(false);

  if (!product) return null;

  const formatPrice = (amount: number) => {
    return amount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  };

  const toggleAddOn = (id: string) => {
    soundManager.playTick();
    setSelectedAddOnIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const selectedAddOnsObjects = ADDONS_CATALOG.filter((a) => selectedAddOnIds.includes(a.id));
  const addOnsTotal = selectedAddOnsObjects.reduce((acc, curr) => acc + curr.price, 0);
  const totalPrice = product.price * quantity + addOnsTotal;

  const handleAdd = () => {
    soundManager.playPluck();
    onAddToCart(product, quantity, cardMessage, selectedAddOnsObjects);
    setShowAddedAlert(true);
    setTimeout(() => {
      setShowAddedAlert(false);
      onClose();
    }, 900);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 lg:p-6 overflow-y-auto">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/75 backdrop-blur-md"
          />

          {/* Modal Card */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.3 }}
            className="relative w-full max-w-5xl bg-white dark:bg-neutral-900 rounded-3xl shadow-2xl border border-neutral-200 dark:border-neutral-800 overflow-y-auto md:overflow-hidden overscroll-contain z-10 max-h-[92vh] max-h-[92dvh] flex flex-col md:flex-row my-auto"
          >
            {/* Close Button */}
            <button
              id="btn-close-modal"
              onClick={onClose}
              className="absolute top-4 right-4 z-20 p-2 rounded-full bg-black/40 hover:bg-black/60 text-white backdrop-blur-md transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Left: 3D Image Gallery */}
            <div className="md:w-1/2 p-5 sm:p-8 bg-neutral-50 dark:bg-neutral-950/50 flex flex-col justify-between">
              <div className="relative aspect-square w-full rounded-2xl overflow-hidden border border-neutral-200 dark:border-neutral-800 shadow-inner group">
                <SafeImage
                  src={product.images[selectedImageIndex] || product.images[0]}
                  alt={product.title[lang]}
                  decoding="async"
                  className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500"
                />
                {product.dimensions && (
                  <div className="absolute top-3 left-3 px-3 py-1 rounded-full bg-black/60 text-white text-xs tabular-nums">
                    {product.dimensions}
                  </div>
                )}
              </div>

              {/* Thumbnails */}
              {product.images.length > 1 && (
                <div className="flex gap-3 mt-4 overflow-x-auto pb-1">
                  {product.images.map((img, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        soundManager.playTick();
                        setSelectedImageIndex(idx);
                      }}
                      className={`relative w-16 h-16 rounded-xl overflow-hidden shrink-0 border-2 transition-all cursor-pointer ${
                        selectedImageIndex === idx
                          ? 'border-amber-500 scale-105 shadow-md'
                          : 'border-transparent opacity-60 hover:opacity-100'
                      }`}
                    >
                      <img src={img} alt="Thumbnail" referrerPolicy="no-referrer" className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Right: Product Details, Add-ons & Calligraphy Card */}
            <div className="md:w-1/2 p-6 sm:p-8 md:overflow-y-auto md:max-h-[85vh] flex flex-col justify-between">
              <div>
                {/* Brand & Rating */}
                <div className="flex items-center justify-between text-xs text-neutral-500 dark:text-neutral-400 mb-2">
                  <span className="uppercase tracking-widest text-xs font-bold text-amber-600 dark:text-amber-400">
                    {product.brand === 'secret_flowers'
                      ? 'Secret Flowers • @secret_tashkent'
                      : product.brand === 'green_mood'
                      ? 'Green Mood • @greenmood_uz'
                      : 'Secret Berries • @secretberries_tashkent'}
                  </span>
                  {product.reviewsCount > 0 && <div className="flex items-center gap-1.5 font-medium">
                    <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                    <span className="text-neutral-800 dark:text-neutral-200">{product.rating}</span>
                    <span className="text-neutral-400">({product.reviewsCount} {t.reviews})</span>
                  </div>}
                </div>

                {/* Title */}
                <h2 className="font-serif text-2xl sm:text-3xl font-light text-neutral-900 dark:text-white leading-tight mb-2">
                  {product.title[lang]}
                </h2>
                <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 font-light mb-4">
                  {product.subtitle[lang]}
                </p>

                {/* Price Display */}
                <div className="flex items-baseline gap-3 mb-6">
                  <span className="font-serif text-2xl sm:text-3xl font-semibold text-neutral-900 dark:text-amber-300">
                    {formatPrice(totalPrice)} {t.uzs}
                  </span>
                  {product.oldPrice && (
                    <span className="text-sm text-neutral-400 line-through">
                      {formatPrice(product.oldPrice * quantity)} {t.uzs}
                    </span>
                  )}
                </div>

                {/* Tabs: Description / Composition / Care / Delivery */}
                <div className="flex border-b border-neutral-200 dark:border-neutral-800 mb-4 text-xs font-medium">
                  <button
                    onClick={() => setActiveTab('desc')}
                    className={`pb-2 px-2.5 transition-colors border-b-2 cursor-pointer ${
                      activeTab === 'desc'
                        ? 'border-amber-500 text-amber-600 dark:text-amber-400'
                        : 'border-transparent text-neutral-500 hover:text-neutral-900 dark:hover:text-white'
                    }`}
                  >
                    {t.detailsTabDesc}
                  </button>
                  <button
                    onClick={() => setActiveTab('comp')}
                    className={`pb-2 px-2.5 transition-colors border-b-2 cursor-pointer ${
                      activeTab === 'comp'
                        ? 'border-amber-500 text-amber-600 dark:text-amber-400'
                        : 'border-transparent text-neutral-500 hover:text-neutral-900 dark:hover:text-white'
                    }`}
                  >
                    {t.detailsTabComp}
                  </button>
                  <button
                    onClick={() => setActiveTab('care')}
                    className={`pb-2 px-2.5 transition-colors border-b-2 cursor-pointer ${
                      activeTab === 'care'
                        ? 'border-amber-500 text-amber-600 dark:text-amber-400'
                        : 'border-transparent text-neutral-500 hover:text-neutral-900 dark:hover:text-white'
                    }`}
                  >
                    {t.detailsTabCare}
                  </button>
                  <button
                    onClick={() => setActiveTab('delivery')}
                    className={`pb-2 px-2.5 transition-colors border-b-2 cursor-pointer ${
                      activeTab === 'delivery'
                        ? 'border-amber-500 text-amber-600 dark:text-amber-400'
                        : 'border-transparent text-neutral-500 hover:text-neutral-900 dark:hover:text-white'
                    }`}
                  >
                    {t.detailsTabDelivery}
                  </button>
                </div>

                {/* Tab Content */}
                <div className="text-xs sm:text-sm text-neutral-600 dark:text-neutral-300 font-light min-h-[75px] mb-6">
                  {activeTab === 'desc' && <p>{product.description[lang]}</p>}
                  {activeTab === 'comp' && (
                    <ul className="space-y-1.5">
                      {product.composition[lang].map((item, i) => (
                        <li key={i} className="flex items-center gap-2">
                          <Check className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  {activeTab === 'care' && (
                    <ul className="space-y-1.5">
                      {product.careTips[lang].map((tip, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-500 mt-1.5 shrink-0" />
                          <span>{tip}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  {activeTab === 'delivery' && (
                    <div className="space-y-2">
                      <p className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-medium">
                        <Truck className="w-4 h-4 shrink-0" />
                        <span>{t.heroFeatureExpress}</span>
                      </p>
                      <p className="text-xs text-neutral-500 dark:text-neutral-400">
                        {t.deliveryNote}
                      </p>
                    </div>
                  )}
                </div>

                {/* Personalized Calligraphy Card Section */}
                <div className="p-4 rounded-2xl bg-neutral-50 dark:bg-neutral-950/60 border border-neutral-200 dark:border-neutral-800 mb-6">
                  <label className="block text-xs font-semibold text-neutral-800 dark:text-neutral-200 mb-2">
                    {t.personalizedCardLabel}
                  </label>
                  <textarea
                    rows={2}
                    value={cardMessage}
                    onChange={(e) => setCardMessage(e.target.value)}
                    placeholder={t.cardPlaceholder}
                    className="w-full text-xs p-3 rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-900 text-neutral-800 dark:text-neutral-100 placeholder-neutral-400 focus:outline-none focus:border-amber-500"
                  />

                  {/* Calligraphy Real-time Preview */}
                  {cardMessage.trim() && (
                    <div className="mt-3 p-3 rounded-xl bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-800/40">
                      <div className="flex items-center justify-between text-xs uppercase tabular-nums tracking-widest text-amber-700 dark:text-amber-400 mb-1">
                        <span>{t.previewCardBadge}</span>
                        <span>{t.waxSealName}</span>
                      </div>
                      <p className="font-serif italic text-sm text-neutral-800 dark:text-amber-200 leading-relaxed">
                        "{cardMessage}"
                      </p>
                    </div>
                  )}
                </div>

                {/* Add-ons Selector */}
                <div className="mb-6">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400 mb-3">
                    {t.addOnsHeading}
                  </h4>
                  <div className="grid grid-cols-2 gap-2.5">
                    {ADDONS_CATALOG.map((addon) => {
                      const isSelected = selectedAddOnIds.includes(addon.id);
                      return (
                        <div
                          key={addon.id}
                          onClick={() => toggleAddOn(addon.id)}
                          className={`p-2.5 rounded-xl border flex items-center gap-2.5 cursor-pointer transition-all ${
                            isSelected
                              ? 'border-amber-500 bg-amber-50/40 dark:bg-amber-950/30'
                              : 'border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900/50 hover:border-neutral-300'
                          }`}
                        >
                          <img src={addon.image} alt={addon.name[lang]} className="w-10 h-10 rounded-lg object-cover shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium text-neutral-800 dark:text-neutral-200 line-clamp-1">
                              {addon.name[lang]}
                            </p>
                            <p className="text-xs text-amber-600 dark:text-amber-400 tabular-nums">
                              +{formatPrice(addon.price)} {t.uzs}
                            </p>
                          </div>
                          <div className={`w-4 h-4 rounded-full flex items-center justify-center border text-xs ${isSelected ? 'bg-amber-500 border-amber-500 text-neutral-950' : 'border-neutral-400'}`}>
                            {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Bottom Actions */}
              <div className="pt-4 border-t border-neutral-200 dark:border-neutral-800 flex items-center gap-4">
                {/* Quantity counter */}
                <div className="flex items-center border border-neutral-300 dark:border-neutral-700 rounded-full px-2 py-1 bg-white dark:bg-neutral-800">
                  <button
                    onClick={() => {
                      soundManager.playTick();
                      setQuantity((q) => Math.max(1, q - 1));
                    }}
                    className="w-7 h-7 flex items-center justify-center text-neutral-600 dark:text-neutral-300 hover:text-amber-500 font-bold cursor-pointer"
                  >
                    -
                  </button>
                  <span className="w-8 text-center text-xs font-semibold text-neutral-800 dark:text-white">
                    {quantity}
                  </span>
                  <button
                    onClick={() => {
                      soundManager.playTick();
                      setQuantity((q) => q + 1);
                    }}
                    className="w-7 h-7 flex items-center justify-center text-neutral-600 dark:text-neutral-300 hover:text-amber-500 font-bold cursor-pointer"
                  >
                    +
                  </button>
                </div>

                <button
                  id="btn-add-modal-cart"
                  onClick={handleAdd}
                  disabled={product.inStock === false}
                  className="flex-1 py-3.5 px-6 rounded-full bg-gradient-to-r from-neutral-900 to-neutral-800 dark:from-amber-400 dark:to-amber-500 text-white dark:text-neutral-950 font-semibold text-xs sm:text-sm tracking-wide shadow-xl hover:scale-[1.01] transition-transform active:scale-98 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
                >
                  <ShoppingBag className="w-4 h-4" />
                  <span>{product.inStock === false ? SOLD_OUT[lang] : showAddedAlert ? t.addedToCartAlert : t.addToCart}</span>
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
