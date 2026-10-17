import { Instagram, MapPin, Phone, Clock, Sparkles, Heart } from 'lucide-react';
import { Language } from '../types';
import { TRANSLATIONS } from '../translations';
import { SecretLogo } from './SecretLogo';

interface FooterProps {
  lang: Language;
}

export function Footer({ lang }: FooterProps) {
  const t = TRANSLATIONS[lang];

  return (
    <footer className="border-t border-neutral-200 dark:border-neutral-800 bg-neutral-50/90 dark:bg-black text-neutral-600 dark:text-neutral-400 py-16 px-4 sm:px-6 lg:px-8 relative z-10 text-sm sm:text-base transition-colors duration-300">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 mb-12">
        {/* Col 1: Brand & Slogan */}
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <SecretLogo size="lg" />
            <div className="flex flex-col">
              <span className="font-display tracking-[0.25em] text-2xl font-bold text-neutral-900 dark:text-white leading-none">
                SECRET
              </span>
              <span className="text-xs uppercase tracking-[0.28em] text-neutral-500 dark:text-neutral-400 font-sans mt-1">
                FLOWERS AND MORE
              </span>
            </div>
          </div>
          <p className="font-light leading-relaxed">
            {t.footerBrandDesc}
          </p>
          <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400 font-medium text-sm">
            <Clock className="w-5 h-5" />
            <span>{t.footerWorkingHours}</span>
          </div>
        </div>

        {/* Col 2: Three Business Lines & Instagram */}
        <div className="space-y-3">
          <h4 className="font-serif text-lg font-semibold uppercase tracking-wider text-neutral-900 dark:text-white">
            {t.footerInstagram}
          </h4>
          <ul className="space-y-2.5">
            <li>
              <a
                href="https://instagram.com/secret_tashkent"
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-center justify-between p-3.5 min-h-[56px] rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 hover:border-rose-400/60 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <img src="/images/flowers/thumb/fl-05.jpg" alt="" className="w-10 h-10 rounded-full object-cover ring-1 ring-white/40" />
                  <span className="text-neutral-800 dark:text-neutral-200 tabular-nums text-sm">@secret_tashkent</span>
                </div>
                <Instagram className="w-5 h-5 text-pink-500" />
              </a>
            </li>
            <li>
              <a
                href="https://instagram.com/greenmood_uz"
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-center justify-between p-3.5 min-h-[56px] rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 hover:border-emerald-400/60 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <img src="/images/plants/thumb/gm-04.jpg" alt="" className="w-10 h-10 rounded-full object-cover ring-1 ring-white/40" />
                  <span className="text-neutral-800 dark:text-neutral-200 tabular-nums text-sm">@greenmood_uz</span>
                </div>
                <Instagram className="w-5 h-5 text-pink-500" />
              </a>
            </li>
            <li>
              <a
                href="https://instagram.com/secretberries_tashkent"
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-center justify-between p-3.5 min-h-[56px] rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 hover:border-amber-400/60 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <img src="/images/berries/thumb/sb-03.jpg" alt="" className="w-10 h-10 rounded-full object-cover ring-1 ring-white/40" />
                  <span className="text-neutral-800 dark:text-neutral-200 tabular-nums text-sm">@secretberries_tashkent</span>
                </div>
                <Instagram className="w-5 h-5 text-pink-500" />
              </a>
            </li>
          </ul>
        </div>

        {/* Col 3: Tashkent Boutique Location & Contacts */}
        <div className="space-y-3">
          <h4 className="font-serif text-lg font-semibold uppercase tracking-wider text-neutral-900 dark:text-white">
            {t.footerBoutique}
          </h4>
          <div className="space-y-2 font-light">
            <p className="flex items-start gap-2">
              <MapPin className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
              <span>{t.footerAddresses}</span>
            </p>
            <p className="flex items-center gap-2">
              <Phone className="w-5 h-5 text-amber-500 shrink-0" />
              <a href="tel:+998712004488" className="tabular-nums hover:text-amber-500 transition-colors">
                +998 (71) 200-44-88
              </a>
            </p>
            <p className="text-sm text-neutral-400 pl-7">
              {t.footerCourier}
            </p>
          </div>
        </div>

        {/* Col 4: Integrated Payment Systems */}
        <div className="space-y-3">
          <h4 className="font-serif text-lg font-semibold uppercase tracking-wider text-neutral-900 dark:text-white">
            {t.footerPayments}
          </h4>
          <p className="text-sm font-light">
            {t.footerPaymentsNote}
          </p>
          <div className="flex flex-wrap gap-2">
            <span className="px-4 py-2 rounded-xl bg-[#00CCCC]/15 text-[#009999] dark:text-[#00CCCC] font-bold text-sm tabular-nums border border-[#00CCCC]/30">
              Payme
            </span>
            <span className="px-4 py-2 rounded-xl bg-[#0070BA]/15 text-[#0070BA] font-bold text-sm tabular-nums border border-[#0070BA]/30">
              Click Up
            </span>
            <span className="px-4 py-2 rounded-xl bg-[#7000FF]/15 text-[#7000FF] font-bold text-sm tabular-nums border border-[#7000FF]/30">
              Uzum Pay
            </span>
            <span className="px-4 py-2 rounded-xl bg-neutral-200 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 font-bold text-sm tabular-nums">
              Humo / Uzcard
            </span>
            <span className="px-4 py-2 rounded-xl bg-neutral-200 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 font-bold text-sm tabular-nums">
              Visa / Mastercard
            </span>
          </div>
        </div>
      </div>

      {/* Bottom Copyright */}
      <div className="max-w-7xl mx-auto pt-8 border-t border-neutral-200 dark:border-neutral-800 flex flex-col sm:flex-row items-center justify-between text-sm text-neutral-400 gap-3">
        <p className="text-center sm:text-left">© 2026 Secret, Tashkent. {t.footerRights}</p>
        <p className="flex items-center gap-1.5 text-center sm:text-right">
          <Heart className="w-4 h-4 text-rose-500 fill-rose-500 shrink-0" />
          <span>{t.footerCrafted}</span>
        </p>
      </div>
    </footer>
  );
}
