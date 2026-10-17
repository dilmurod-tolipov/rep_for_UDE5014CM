import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, ShieldCheck, ArrowRight, User, Phone, MapPin, Clock, CreditCard, Sparkles, Banknote } from 'lucide-react';
import { CartItem, Language, PaymentMethod, Order } from '../types';
import { TRANSLATIONS } from '../translations';
import { TASHKENT_DISTRICTS } from '../data/products';
import { soundManager } from '../utils/audio';

interface CheckoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  cartItems: CartItem[];
  lang: Language;
  onOrderPlaced: (order: Order) => void;
}

import { DemoPaymentNote } from './DemoNotice';

export function CheckoutModal({ isOpen, onClose, cartItems, lang, onOrderPlaced }: CheckoutModalProps) {
  const t = TRANSLATIONS[lang];

  // Customer form state
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');

  // Recipient form state
  const [isSelfRecipient, setIsSelfRecipient] = useState(false);
  const [recipientName, setRecipientName] = useState('');
  const [recipientPhone, setRecipientPhone] = useState('');
  const [isSurprise, setIsSurprise] = useState(false);

  // Address form state
  const [district, setDistrict] = useState(TASHKENT_DISTRICTS[0]);
  const [address, setAddress] = useState('');
  const [apartment, setApartment] = useState('');
  const [landmark, setLandmark] = useState('');

  // Delivery options
  const [deliveryType, setDeliveryType] = useState<'express' | 'scheduled'>('express');
  const [selectedDate, setSelectedDate] = useState('today');
  const [timeSlot, setTimeSlot] = useState('10:00 - 12:00');

  // Payment method
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('payme');

  const calculateItemTotal = (item: CartItem) => {
    const addOnsPrice = item.selectedAddOns.reduce((acc, curr) => acc + curr.price, 0);
    return (item.product.price + addOnsPrice) * item.quantity;
  };

  const subtotal = cartItems.reduce((acc, item) => acc + calculateItemTotal(item), 0);
  const deliveryFee = subtotal >= 500000 || subtotal === 0 ? 0 : 35000;
  const total = subtotal + deliveryFee;

  const formatPrice = (amount: number) => {
    return amount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    soundManager.playTick();

    const newOrder: Order = {
      id: `ord-${Date.now()}`,
      orderNumber: `SEC-${Math.floor(1000 + Math.random() * 9000)}`,
      createdAt: new Date().toISOString(),
      brand: 'mixed',
      items: cartItems.map((ci) => ({
        productId: ci.product.id,
        productTitle: ci.product.title,
        productImage: ci.product.images[0],
        quantity: ci.quantity,
        price: ci.product.price,
        brand: ci.product.brand,
        cardMessage: ci.cardMessage
      })),
      customer: {
        name: customerName,
        phone: customerPhone,
        email: customerEmail
      },
      recipient: {
        isRecipientCustomer: isSelfRecipient,
        name: isSelfRecipient ? customerName : recipientName,
        phone: isSelfRecipient ? customerPhone : recipientPhone,
        isSurprise
      },
      delivery: {
        district,
        address,
        apartment,
        landmark,
        date: ({ today: t.dayToday, tomorrow: t.dayTomorrow, after: t.dayAfter } as Record<string, string>)[selectedDate] || selectedDate,
        timeSlot: deliveryType === 'express' ? t.deliveryExpress : timeSlot,
        type: deliveryType
      },
      payment: {
        method: paymentMethod,
        status: paymentMethod === 'cash' ? 'cash_on_delivery' : 'pending'
      },
      status: 'new',
      subtotal,
      deliveryFee,
      discount: 0,
      total,
      notes: isSurprise ? 'Surprise gift: do not reveal sender or content before delivery.' : undefined
    };

    onOrderPlaced(newOrder);
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

          {/* Modal Container */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative w-full max-w-3xl bg-white dark:bg-neutral-900 rounded-3xl shadow-2xl border border-neutral-200 dark:border-neutral-800 overflow-hidden z-10 max-h-[92vh] max-h-[92dvh] flex flex-col my-auto"
          >
            {/* Header */}
            <div className="p-6 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between bg-neutral-50/50 dark:bg-neutral-950/40">
              <div>
                <h2 className="font-serif text-2xl font-light text-neutral-900 dark:text-white">
                  {t.checkoutTitle}
                </h2>
                <p className="text-xs text-neutral-500 font-light mt-0.5">
                  {t.checkoutSubtitle}
                </p>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-full hover:bg-neutral-200 dark:hover:bg-neutral-800 text-neutral-500 transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Form Body */}
            <form onSubmit={handleSubmit} className="p-5 sm:p-8 overflow-y-auto overscroll-contain space-y-8 flex-1 min-h-0">
              {/* Section 1: Customer Info */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400 mb-4 flex items-center gap-2">
                  <User className="w-4 h-4" />
                  <span>{t.customerInfo}</span>
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1.5">
                      {t.yourName} *
                    </label>
                    <input
                      type="text"
                      required
                      value={customerName}
                      onChange={(e) => setCustomerName(e.target.value)}
                      className="w-full text-xs p-3 rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white focus:outline-none focus:border-amber-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1.5">
                      {t.yourPhone} *
                    </label>
                    <input
                      type="tel"
                      inputMode="tel"
                      placeholder="+998 __ ___ __ __"
                      required
                      value={customerPhone}
                      onChange={(e) => setCustomerPhone(e.target.value)}
                      className="w-full text-xs p-3 rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white focus:outline-none focus:border-amber-500 tabular-nums"
                    />
                  </div>
                </div>
              </div>

              {/* Section 2: Recipient Info */}
              <div className="pt-6 border-t border-neutral-200 dark:border-neutral-800">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-rose-500 flex items-center gap-2">
                    <Sparkles className="w-4 h-4" />
                    <span>{t.recipientInfo}</span>
                  </h3>
                  <label className="flex items-center gap-2 text-xs text-neutral-600 dark:text-neutral-400 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isSelfRecipient}
                      onChange={(e) => setIsSelfRecipient(e.target.checked)}
                      className="rounded border-neutral-300 text-amber-500 focus:ring-amber-500"
                    />
                    <span>{t.sameAsCustomer}</span>
                  </label>
                </div>

                {!isSelfRecipient && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1.5">
                          {t.recipientName} *
                        </label>
                        <input
                          type="text"
                          required
                          value={recipientName}
                          onChange={(e) => setRecipientName(e.target.value)}
                          className="w-full text-xs p-3 rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white focus:outline-none focus:border-rose-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1.5">
                          {t.recipientPhone} *
                        </label>
                        <input
                          type="tel"
                      inputMode="tel"
                      placeholder="+998 __ ___ __ __"
                          required
                          value={recipientPhone}
                          onChange={(e) => setRecipientPhone(e.target.value)}
                          className="w-full text-xs p-3 rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white focus:outline-none focus:border-rose-500 tabular-nums"
                        />
                      </div>
                    </div>

                    <label className="flex items-start gap-2.5 p-3 rounded-xl bg-rose-50/50 dark:bg-rose-950/20 border border-rose-200/50 dark:border-rose-900/30 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={isSurprise}
                        onChange={(e) => setIsSurprise(e.target.checked)}
                        className="mt-0.5 rounded border-rose-300 text-rose-600 focus:ring-rose-500"
                      />
                      <span className="text-xs text-neutral-700 dark:text-neutral-300 leading-snug">
                        {t.surpriseOption}
                      </span>
                    </label>
                  </div>
                )}
              </div>

              {/* Section 3: Delivery Address in Tashkent */}
              <div className="pt-6 border-t border-neutral-200 dark:border-neutral-800">
                <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 mb-4 flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  <span>{t.deliveryAddress}</span>
                </h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1.5">
                      {t.selectDistrict} *
                    </label>
                    <select
                      value={district}
                      onChange={(e) => setDistrict(e.target.value)}
                      className="w-full text-xs p-3 rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white focus:outline-none focus:border-emerald-500"
                    >
                      {TASHKENT_DISTRICTS.map((d) => (
                        <option key={d} value={d}>
                          {d}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1.5">
                        {t.streetAddress} *
                      </label>
                      <input
                        type="text"
                        required
                        value={address}
                        onChange={(e) => setAddress(e.target.value)}
                        className="w-full text-xs p-3 rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white focus:outline-none focus:border-emerald-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-neutral-700 dark:text-neutral-300 mb-1.5">
                        {t.apartmentNumber}
                      </label>
                      <input
                        type="text"
                        value={apartment}
                        onChange={(e) => setApartment(e.target.value)}
                        className="w-full text-xs p-3 rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white focus:outline-none focus:border-emerald-500"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Section 4: Delivery Time */}
              <div className="pt-6 border-t border-neutral-200 dark:border-neutral-800">
                <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-500 mb-4 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-amber-500" />
                  <span>{t.deliveryTimeTitle}</span>
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
                  <button
                    type="button"
                    onClick={() => {
                      soundManager.playTick();
                      setDeliveryType('express');
                    }}
                    className={`p-3.5 rounded-2xl border text-left cursor-pointer transition-all ${
                      deliveryType === 'express'
                        ? 'border-amber-500 bg-amber-50/50 dark:bg-amber-950/40 font-semibold ring-1 ring-amber-500'
                        : 'border-neutral-200 dark:border-neutral-800 opacity-70'
                    }`}
                  >
                    <p className="text-xs text-neutral-900 dark:text-white">{t.deliveryExpress}</p>
                    <p className="text-xs text-neutral-500 mt-1 font-light">{t.expressHint}</p>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      soundManager.playTick();
                      setDeliveryType('scheduled');
                    }}
                    className={`p-3.5 rounded-2xl border text-left cursor-pointer transition-all ${
                      deliveryType === 'scheduled'
                        ? 'border-amber-500 bg-amber-50/50 dark:bg-amber-950/40 font-semibold ring-1 ring-amber-500'
                        : 'border-neutral-200 dark:border-neutral-800 opacity-70'
                    }`}
                  >
                    <p className="text-xs text-neutral-900 dark:text-white">{t.deliveryScheduled}</p>
                    <p className="text-xs text-neutral-500 mt-1 font-light">{t.scheduledHint}</p>
                  </button>
                </div>

                {deliveryType === 'scheduled' && (
                  <div className="grid grid-cols-2 gap-3 mt-3">
                    <select
                      value={selectedDate}
                      onChange={(e) => setSelectedDate(e.target.value)}
                      className="text-xs p-2.5 rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white"
                    >
                      <option value="today">{t.dayToday}</option>
                      <option value="tomorrow">{t.dayTomorrow}</option>
                      <option value="after">{t.dayAfter}</option>
                    </select>

                    <select
                      value={timeSlot}
                      onChange={(e) => setTimeSlot(e.target.value)}
                      className="text-xs p-2.5 rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white"
                    >
                      <option>10:00 - 12:00</option>
                      <option>12:00 - 14:00</option>
                      <option>14:00 - 16:00</option>
                      <option>16:00 - 18:00</option>
                      <option>18:00 - 20:00</option>
                      <option>20:00 - 22:00</option>
                    </select>
                  </div>
                )}
              </div>

              {/* Section 5: Payment Gateways Integration */}
              <div className="pt-6 border-t border-neutral-200 dark:border-neutral-800">
                <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-500 mb-4 flex items-center gap-2">
                  <CreditCard className="w-4 h-4 text-emerald-500" />
                  <span>{t.paymentMethodTitle}</span>
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* Payme */}
                  <label
                    onClick={() => {
                      soundManager.playTick();
                      setPaymentMethod('payme');
                    }}
                    className={`p-3.5 rounded-2xl border flex items-center gap-3 cursor-pointer transition-all ${
                      paymentMethod === 'payme'
                        ? 'border-[#00CCCC] bg-[#00CCCC]/10 ring-1 ring-[#00CCCC]'
                        : 'border-neutral-200 dark:border-neutral-800 hover:border-neutral-300'
                    }`}
                  >
                    <input type="radio" name="pm" checked={paymentMethod === 'payme'} onChange={() => {}} className="hidden" />
                    <div className="w-9 h-9 rounded-xl bg-[#00CCCC] text-neutral-950 font-black flex items-center justify-center text-xs shrink-0">
                      P
                    </div>
                    <div>
                      <p className="text-xs font-bold text-neutral-900 dark:text-white">Payme</p>
                      <p className="text-xs text-neutral-500 font-light">{t.paymeDesc}</p>
                    </div>
                  </label>

                  {/* Click */}
                  <label
                    onClick={() => {
                      soundManager.playTick();
                      setPaymentMethod('click');
                    }}
                    className={`p-3.5 rounded-2xl border flex items-center gap-3 cursor-pointer transition-all ${
                      paymentMethod === 'click'
                        ? 'border-[#0070BA] bg-[#0070BA]/10 ring-1 ring-[#0070BA]'
                        : 'border-neutral-200 dark:border-neutral-800 hover:border-neutral-300'
                    }`}
                  >
                    <input type="radio" name="pm" checked={paymentMethod === 'click'} onChange={() => {}} className="hidden" />
                    <div className="w-9 h-9 rounded-xl bg-[#0070BA] text-white font-black flex items-center justify-center text-xs shrink-0">
                      C
                    </div>
                    <div>
                      <p className="text-xs font-bold text-neutral-900 dark:text-white">Click Up</p>
                      <p className="text-xs text-neutral-500 font-light">{t.clickDesc}</p>
                    </div>
                  </label>

                  {/* Uzum Pay */}
                  <label
                    onClick={() => {
                      soundManager.playTick();
                      setPaymentMethod('uzumpay');
                    }}
                    className={`p-3.5 rounded-2xl border flex items-center gap-3 cursor-pointer transition-all ${
                      paymentMethod === 'uzumpay'
                        ? 'border-[#7000FF] bg-[#7000FF]/10 ring-1 ring-[#7000FF]'
                        : 'border-neutral-200 dark:border-neutral-800 hover:border-neutral-300'
                    }`}
                  >
                    <input type="radio" name="pm" checked={paymentMethod === 'uzumpay'} onChange={() => {}} className="hidden" />
                    <div className="w-9 h-9 rounded-xl bg-[#7000FF] text-white font-black flex items-center justify-center text-xs shrink-0">
                      U
                    </div>
                    <div>
                      <p className="text-xs font-bold text-neutral-900 dark:text-white">Uzum Pay</p>
                      <p className="text-xs text-neutral-500 font-light">{t.uzumpayDesc}</p>
                    </div>
                  </label>

                  {/* Cash or Card to Courier */}
                  <label
                    onClick={() => {
                      soundManager.playTick();
                      setPaymentMethod('cash');
                    }}
                    className={`p-3.5 rounded-2xl border flex items-center gap-3 cursor-pointer transition-all ${
                      paymentMethod === 'cash'
                        ? 'border-amber-500 bg-amber-500/10 ring-1 ring-amber-500'
                        : 'border-neutral-200 dark:border-neutral-800 hover:border-neutral-300'
                    }`}
                  >
                    <input type="radio" name="pm" checked={paymentMethod === 'cash'} onChange={() => {}} className="hidden" />
                    <div className="w-9 h-9 rounded-xl bg-amber-500 text-neutral-950 font-black flex items-center justify-center text-xs shrink-0">
                      <Banknote className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-neutral-900 dark:text-white">{t.cashTitle}</p>
                      <p className="text-xs text-neutral-500 font-light">{t.cashDesc}</p>
                    </div>
                  </label>
                </div>
              </div>

              {/* Submit & Breakdown */}
              <div className="pt-6 border-t border-neutral-200 dark:border-neutral-800 space-y-4">
                <div className="p-4 rounded-2xl bg-neutral-50 dark:bg-neutral-950/50 border border-neutral-200 dark:border-neutral-800 space-y-2 text-xs">
                  <div className="flex justify-between text-neutral-500">
                    <span>{t.subtotal}</span>
                    <span className="tabular-nums text-neutral-900 dark:text-white">{formatPrice(subtotal)} {t.uzs}</span>
                  </div>
                  <div className="flex justify-between text-neutral-500">
                    <span>{t.deliveryFee}</span>
                    <span className="tabular-nums text-neutral-900 dark:text-white">{formatPrice(deliveryFee)} {t.uzs}</span>
                  </div>
                  <div className="flex justify-between font-bold text-sm text-neutral-900 dark:text-white pt-2 border-t border-neutral-200 dark:border-neutral-800">
                    <span>{t.total}</span>
                    <span className="font-serif text-lg text-amber-600 dark:text-amber-400">
                      {formatPrice(total)} {t.uzs}
                    </span>
                  </div>
                </div>

                <DemoPaymentNote lang={lang} />
                <button
                  type="submit"
                  id="btn-submit-order"
                  className="w-full py-4 rounded-full bg-gradient-to-r from-neutral-900 to-neutral-800 dark:from-amber-400 dark:to-amber-500 text-white dark:text-neutral-950 font-semibold text-sm tracking-wide shadow-xl hover:scale-[1.01] active:scale-98 transition-transform flex items-center justify-center gap-2 cursor-pointer"
                >
                  <ShieldCheck className="w-4 h-4" />
                  <span>{t.placeOrderBtn}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
