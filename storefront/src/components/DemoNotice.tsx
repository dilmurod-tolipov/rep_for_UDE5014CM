import { Language } from '../types';

/**
 * DEMO MODE switch. While true, the site shows a "demo" bar and payment notes,
 * so no visitor thinks an order or payment is real.
 * Set to false only once orders are really delivered to the shop and payments are connected.
 */
export const DEMO_MODE = true;

export const DEMO_TEXT: Record<Language, { bar: string; payment: string; done: string }> = {
  uz: {
    bar: 'Demo sayt: buyurtmalar va to‘lovlar haqiqiy emas, kontaktlar vaqtinchalik.',
    payment: 'DEMO: pul yechilmaydi va buyurtma do‘konga yuborilmaydi.',
    done: 'Demo buyurtma: haqiqiy buyurtma yuborilmadi.'
  },
  ru: {
    bar: 'Демо-сайт: заказы и оплата не настоящие, контакты временные.',
    payment: 'ДЕМО: деньги не списываются, заказ в магазин не отправляется.',
    done: 'Демо-заказ: настоящий заказ не отправлен.'
  },
  en: {
    bar: 'Demo site: orders and payments are not real, contacts are placeholders.',
    payment: 'DEMO: no money is charged and the order is not sent to the shop.',
    done: 'Demo order: no real order was sent.'
  }
};

/** Slim bar pinned to the bottom of the screen on every page while DEMO_MODE is on. */
export function DemoBar({ lang }: { lang: Language }) {
  if (!DEMO_MODE) return null;
  return (
    <div
      role="note"
      className="fixed bottom-0 inset-x-0 z-40 px-3 py-2 pb-[calc(0.5rem+env(safe-area-inset-bottom))] bg-amber-400 text-neutral-950 text-[11px] sm:text-xs font-semibold text-center leading-snug shadow-[0_-2px_12px_rgba(0,0,0,0.25)]"
    >
      {DEMO_TEXT[lang].bar}
    </div>
  );
}

/** Inline warning box used inside the payment and checkout screens. */
export function DemoPaymentNote({ lang }: { lang: Language }) {
  if (!DEMO_MODE) return null;
  return (
    <div className="mb-5 px-4 py-3 rounded-2xl bg-amber-400/15 border border-amber-500/50 text-amber-700 dark:text-amber-300 text-xs font-semibold leading-snug">
      {DEMO_TEXT[lang].payment}
    </div>
  );
}
