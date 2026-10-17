import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, ShieldCheck, CheckCircle2, ArrowRight, Smartphone, Sparkles } from 'lucide-react';
import confetti from 'canvas-confetti';
import { PaymentMethod, Language, Order } from '../types';
import { TRANSLATIONS } from '../translations';
import { soundManager } from '../utils/audio';

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  order: Order | null;
  lang: Language;
  onPaymentSuccess: (orderId: string, transactionId: string) => void;
}

import { DemoPaymentNote } from './DemoNotice';

export function PaymentModal({
  isOpen,
  onClose,
  order,
  lang,
  onPaymentSuccess
}: PaymentModalProps) {
  const t = TRANSLATIONS[lang];
  const [step, setStep] = useState<'prompt' | 'processing' | 'success'>('prompt');
  const [smsCode, setSmsCode] = useState('7428');
  const [countdown, setCountdown] = useState(60);

  useEffect(() => {
    if (step === 'prompt') {
      const timer = setInterval(() => {
        setCountdown((c) => (c > 0 ? c - 1 : 60));
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [step]);

  if (!order) return null;

  const formatPrice = (amount: number) => {
    return amount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  };

  const getGatewayBrand = (method: PaymentMethod) => {
    switch (method) {
      case 'payme':
        return { name: 'Payme', color: 'from-[#00CCCC] to-[#009999]', badge: 'bg-[#00CCCC] text-neutral-950' };
      case 'click':
        return { name: 'Click Up', color: 'from-[#0070BA] to-[#003087]', badge: 'bg-[#0070BA] text-white' };
      case 'uzumpay':
        return { name: 'Uzum Pay', color: 'from-[#7000FF] to-[#4D00B3]', badge: 'bg-[#7000FF] text-white' };
      case 'card':
        return { name: 'Humo / Uzcard / Visa', color: 'from-amber-600 to-amber-700', badge: 'bg-amber-600 text-white' };
      default:
        return { name: 'Cash on Delivery', color: 'from-neutral-800 to-neutral-900', badge: 'bg-neutral-800 text-white' };
    }
  };

  const gateway = getGatewayBrand(order.payment.method);

  const handleConfirm = () => {
    soundManager.playTick();
    setStep('processing');

    setTimeout(() => {
      setStep('success');
      soundManager.playSuccessChord();

      // Launch celebration confetti
      try {
        confetti({
          particleCount: 80,
          spread: 70,
          origin: { y: 0.6 }
        });
      } catch {
        // ignore
      }

      const txId = `${order.payment.method.toUpperCase()}-${Math.floor(100000 + Math.random() * 900000)}-UZ`;
      onPaymentSuccess(order.id, txId);
    }, 1400);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={step === 'success' ? onClose : undefined}
            className="fixed inset-0 bg-black/80 backdrop-blur-md"
          />

          {/* Dialog Container */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 15 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 15 }}
            className="relative w-full max-w-lg bg-white dark:bg-neutral-900 rounded-3xl shadow-2xl border border-neutral-200 dark:border-neutral-800 overflow-hidden z-10 p-6 sm:p-8 text-neutral-800 dark:text-neutral-100 my-auto"
          >
            {/* Top Close Button */}
            {step !== 'processing' && (
              <button
                onClick={onClose}
                className="absolute top-5 right-5 p-2 rounded-full text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            )}

            {step === 'prompt' && (
              <div>
                <DemoPaymentNote lang={lang} />
                {/* Gateway Header */}
                <div className="flex items-center gap-3 mb-6">
                  <div className={`px-3 py-1.5 rounded-xl font-bold text-xs tracking-wider uppercase ${gateway.badge}`}>
                    {gateway.name}
                  </div>
                  <div>
                    <h3 className="font-serif text-lg font-semibold leading-none">{t.paymentGatewayTitle}</h3>
                    <p className="text-xs text-neutral-400 tabular-nums mt-0.5">Order #{order.orderNumber}</p>
                  </div>
                </div>

                {/* Amount Box */}
                <div className="p-4 rounded-2xl bg-neutral-50 dark:bg-neutral-950/60 border border-neutral-200 dark:border-neutral-800 mb-6">
                  <div className="flex justify-between items-center text-xs text-neutral-500 mb-1">
                    <span>{t.total}</span>
                    <span className="text-emerald-500 flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5" /> {t.secureLabel}
                    </span>
                  </div>
                  <div className="font-serif text-2xl sm:text-3xl font-bold text-neutral-900 dark:text-amber-300">
                    {formatPrice(order.total)} {t.uzs}
                  </div>
                  <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-2 line-clamp-1">
                    {order.items.map((i) => i.productTitle[lang]).join(', ')}
                  </div>
                </div>

                {/* Verification Code simulation */}
                <div className="space-y-4 mb-6">
                  <div className="flex items-center justify-between text-xs">
                    <label className="font-medium text-neutral-700 dark:text-neutral-300 flex items-center gap-1.5">
                      <Smartphone className="w-3.5 h-3.5 text-amber-500" />
                      <span>{t.smsCodePrompt}</span>
                    </label>
                    <span className="text-xs tabular-nums text-neutral-400">00:{countdown < 10 ? `0${countdown}` : countdown}</span>
                  </div>

                  <div className="flex justify-center gap-2.5">
                    {['7', '4', '2', '8'].map((digit, idx) => (
                      <div
                        key={idx}
                        className="w-12 h-14 rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 flex items-center justify-center tabular-nums text-2xl font-bold text-neutral-900 dark:text-amber-300 shadow-sm"
                      >
                        {digit}
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-center text-neutral-400 italic">
                    SMS code sent to {order.customer.phone}
                  </p>
                </div>

                {/* Confirm button */}
                <button
                  id="btn-confirm-payment"
                  onClick={handleConfirm}
                  className={`w-full py-4 rounded-full bg-gradient-to-r ${gateway.color} text-white font-semibold text-sm shadow-xl hover:scale-[1.01] active:scale-98 transition-all flex items-center justify-center gap-2 cursor-pointer`}
                >
                  <ShieldCheck className="w-4 h-4" />
                  <span>{t.confirmPayment}</span>
                </button>
              </div>
            )}

            {step === 'processing' && (
              <div className="py-12 flex flex-col items-center justify-center text-center">
                <div className="w-16 h-16 rounded-full border-4 border-amber-500/20 border-t-amber-500 animate-spin mb-6" />
                <h3 className="font-serif text-xl font-light text-neutral-900 dark:text-white mb-2">
                  {t.orderProcessing}
                </h3>
                <p className="text-xs text-neutral-400">
                  {gateway.name} Protocol Handshake • 3D Secure 2.0
                </p>
              </div>
            )}

            {step === 'success' && (
              <div className="py-4 text-center">
                <DemoPaymentNote lang={lang} />
                <div className="w-16 h-16 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                  <CheckCircle2 className="w-8 h-8" />
                </div>

                <h3 className="font-serif text-2xl font-light text-neutral-900 dark:text-white mb-2">
                  {t.paymentSuccess}
                </h3>

                <p className="text-xs text-neutral-500 dark:text-neutral-400 font-light mb-6 max-w-sm mx-auto">
                  {t.orderSentToCrm}
                </p>

                {/* Receipt Card */}
                <div className="p-4 rounded-2xl bg-neutral-50 dark:bg-neutral-950/60 border border-neutral-200 dark:border-neutral-800 text-left text-xs space-y-2 mb-6">
                  <div className="flex justify-between">
                    <span className="text-neutral-500">{t.orderRef}</span>
                    <span className="tabular-nums font-bold text-neutral-900 dark:text-white">#{order.orderNumber}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">{t.recipientLabel}</span>
                    <span className="font-medium text-neutral-800 dark:text-neutral-200">{order.recipient.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">{t.addressLabel}</span>
                    <span className="font-medium text-neutral-800 dark:text-neutral-200">{order.delivery.district}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">{t.deliverySlot}</span>
                    <span className="tabular-nums text-amber-600 dark:text-amber-400">{order.delivery.timeSlot}</span>
                  </div>
                </div>

                {/* Action: Return to Storefront */}
                <div className="pt-2">
                  <button
                    onClick={onClose}
                    className="w-full py-3.5 px-6 rounded-full bg-[#d7a9a3] hover:bg-[#d7a9a3]/90 text-[#291823] font-semibold text-xs tracking-wider uppercase shadow-xl hover:scale-[1.01] transition-transform flex items-center justify-center gap-2 cursor-pointer"
                  >
                    <span>{lang === 'uz' ? 'Xaridni davom ettirish' : lang === 'ru' ? 'Вернуться к витрине' : 'Back to Storefront'}</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
