import { motion, AnimatePresence } from 'motion/react';
import { X, Trash2, ShoppingBag, ArrowRight } from 'lucide-react';
import { CartItem, Language } from '../types';
import { TRANSLATIONS } from '../translations';
import { SecretLogo } from './SecretLogo';
import { soundManager } from '../utils/audio';

interface CartDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  items: CartItem[];
  lang: Language;
  onUpdateQuantity: (cartItemId: string, newQty: number) => void;
  onRemoveItem: (cartItemId: string) => void;
  onProceedToCheckout: () => void;
}

import { thumbOf } from './SafeImage';

export function CartDrawer({
  isOpen,
  onClose,
  items,
  lang,
  onUpdateQuantity,
  onRemoveItem,
  onProceedToCheckout
}: CartDrawerProps) {
  const t = TRANSLATIONS[lang];

  const formatPrice = (amount: number) => {
    return amount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  };

  const calculateItemTotal = (item: CartItem) => {
    const addOnsPrice = item.selectedAddOns.reduce((acc, curr) => acc + curr.price, 0);
    return (item.product.price + addOnsPrice) * item.quantity;
  };

  const subtotal = items.reduce((acc, item) => acc + calculateItemTotal(item), 0);
  const deliveryFee = subtotal >= 500000 || subtotal === 0 ? 0 : 35000;
  const total = subtotal + deliveryFee;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
          />

          <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 28, stiffness: 280 }}
              className="w-screen max-w-md bg-white dark:bg-neutral-900 shadow-2xl border-l border-neutral-200 dark:border-neutral-800 flex flex-col justify-between"
            >
              {/* Drawer Header */}
              <div className="p-6 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <SecretLogo size="xs" />
                  <h2 className="font-serif text-xl font-light text-neutral-900 dark:text-white">
                    {t.cartTitle} ({items.reduce((acc, i) => acc + i.quantity, 0)})
                  </h2>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-full hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-500 transition-colors cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Items List */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {items.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center p-8 text-neutral-400">
                    <ShoppingBag className="w-12 h-12 stroke-[1.2] mb-3 text-neutral-300 dark:text-neutral-600" />
                    <p className="text-sm font-light">{t.cartEmpty}</p>
                  </div>
                ) : (
                  items.map((item) => (
                    <div
                      key={item.cartItemId}
                      className="p-4 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-950/40 flex gap-4"
                    >
                      <img
                        src={thumbOf(item.product.images[0])}
                        loading="lazy"
                        alt={item.product.title[lang]}
                        className="w-20 h-20 rounded-xl object-cover shrink-0"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-start">
                          <h4 className="font-serif text-sm font-medium text-neutral-900 dark:text-white line-clamp-1">
                            {item.product.title[lang]}
                          </h4>
                          <button
                            onClick={() => {
                              soundManager.playTick();
                              onRemoveItem(item.cartItemId);
                            }}
                            className="text-neutral-400 hover:text-rose-500 transition-colors ml-2 cursor-pointer"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>

                        {/* Add-ons mini summary */}
                        {item.selectedAddOns.length > 0 && (
                          <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-1 line-clamp-1">
                            + {item.selectedAddOns.map((a) => a.name[lang]).join(', ')}
                          </div>
                        )}

                        {item.cardMessage && (
                          <p className="text-xs italic text-amber-600 dark:text-amber-400 mt-0.5 line-clamp-1">
                            "{item.cardMessage}"
                          </p>
                        )}

                        <div className="flex items-center justify-between mt-3">
                          <span className="font-serif text-sm font-semibold text-neutral-900 dark:text-amber-300">
                            {formatPrice(calculateItemTotal(item))} {t.uzs}
                          </span>

                          {/* Qty controls */}
                          <div className="flex items-center border border-neutral-300 dark:border-neutral-700 rounded-full px-2 py-0.5 bg-white dark:bg-neutral-900">
                            <button
                              onClick={() => {
                                soundManager.playTick();
                                onUpdateQuantity(item.cartItemId, item.quantity - 1);
                              }}
                              className="w-5 text-center text-xs font-bold text-neutral-500 hover:text-neutral-900 dark:hover:text-white cursor-pointer"
                            >
                              -
                            </button>
                            <span className="w-5 text-center text-xs font-medium text-neutral-800 dark:text-white">
                              {item.quantity}
                            </span>
                            <button
                              onClick={() => {
                                soundManager.playTick();
                                onUpdateQuantity(item.cartItemId, item.quantity + 1);
                              }}
                              className="w-5 text-center text-xs font-bold text-neutral-500 hover:text-neutral-900 dark:hover:text-white cursor-pointer"
                            >
                              +
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Drawer Footer & Checkout */}
              {items.length > 0 && (
                <div className="p-6 border-t border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 space-y-3">
                  <div className="space-y-1.5 text-xs text-neutral-600 dark:text-neutral-400">
                    <div className="flex justify-between">
                      <span>{t.subtotal}</span>
                      <span className="tabular-nums text-neutral-900 dark:text-white">{formatPrice(subtotal)} {t.uzs}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>{t.deliveryFee}</span>
                      {deliveryFee === 0 ? (
                        <span className="font-semibold text-emerald-600 dark:text-emerald-400 uppercase text-xs">
                          {t.freeDelivery}
                        </span>
                      ) : (
                        <span className="tabular-nums text-neutral-900 dark:text-white">{formatPrice(deliveryFee)} {t.uzs}</span>
                      )}
                    </div>
                    <div className="flex justify-between text-sm font-semibold text-neutral-900 dark:text-white pt-2 border-t border-neutral-100 dark:border-neutral-800">
                      <span>{t.total}</span>
                      <span className="font-serif text-lg text-[#291823] dark:text-[#d7a9a3]">
                        {formatPrice(total)} {t.uzs}
                      </span>
                    </div>
                  </div>

                  <button
                    id="btn-proceed-checkout"
                    onClick={() => {
                      soundManager.playChime(880);
                      onProceedToCheckout();
                    }}
                    className="w-full py-4 rounded-full bg-[#291823] text-[#d7a9a3] dark:bg-[#d7a9a3] dark:text-[#291823] font-semibold text-sm tracking-wide shadow-xl hover:scale-[1.01] transition-transform active:scale-98 flex items-center justify-center gap-2 cursor-pointer border border-[#d7a9a3]/40"
                  >
                    <span>{t.proceedToCheckout}</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              )}
            </motion.div>
          </div>
        </div>
      )}
    </AnimatePresence>
  );
}
