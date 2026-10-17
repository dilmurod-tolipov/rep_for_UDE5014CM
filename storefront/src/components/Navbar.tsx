import { useState, useEffect } from 'react';
import { ShoppingBag, Sparkles, Menu, X, Instagram } from 'lucide-react';
import { Language } from '../types';
import { TRANSLATIONS } from '../translations';
import { LanguageSelector } from './LanguageSelector';
import { SecretLogo } from './SecretLogo';
import { soundManager } from '../utils/audio';

interface NavbarProps {
  lang: Language;
  cartCount: number;
  onOpenCart: () => void;
  onSelectLanguage: (lang: Language) => void;
  onNavigateTo: (sectionId: string) => void;
}

export function Navbar({
  lang,
  cartCount,
  onOpenCart,
  onSelectLanguage,
  onNavigateTo
}: NavbarProps) {
  const t = TRANSLATIONS[lang];
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-40 transition-all duration-300 ${
        isScrolled
          ? 'bg-white/95 dark:bg-black/90 backdrop-blur-xl border-b border-neutral-200 dark:border-neutral-800/80 shadow-sm py-3'
          : 'bg-transparent py-4 sm:py-5'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        {/* Brand Logo with User-Uploaded Asset */}
        <div
          onClick={() => {
            soundManager.playChime(880);
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }}
          className="flex items-center gap-3 cursor-pointer group select-none"
        >
          <SecretLogo size="sm" className="group-hover:scale-105 transition-transform duration-300 shadow-sm" />
          <div className="flex flex-col">
            <span className="font-display tracking-[0.25em] text-lg sm:text-xl font-bold text-neutral-900 dark:text-[#f5ecea] group-hover:text-[#d7a9a3] transition-colors leading-none">
              SECRET
            </span>
            <span className="block text-[8.5px] uppercase tracking-[0.28em] text-neutral-500 dark:text-[#d7a9a3]/70 font-sans mt-0.5">
              FLOWERS AND MORE
            </span>
          </div>
        </div>

        {/* Desktop Navigation Links */}
        <nav className="hidden lg:flex items-center gap-8 text-xs font-medium uppercase tracking-widest text-neutral-600 dark:text-neutral-300">
          <button
            onClick={() => onNavigateTo('section-catalog')}
            className="hover:text-[#d7a9a3] transition-colors cursor-pointer"
          >
            {t.navCatalog}
          </button>
          <button
            onClick={() => onNavigateTo('section-atelier')}
            className="hover:text-[#d7a9a3] transition-colors flex items-center gap-1 cursor-pointer"
          >
            <span>{t.navAtelier}</span>
          </button>
          <button
            onClick={() => onNavigateTo('section-brands')}
            className="hover:text-[#d7a9a3] transition-colors cursor-pointer"
          >
            {t.navAbout}
          </button>
        </nav>

        {/* Right Action Icons & Controls */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Language Switcher */}
          <LanguageSelector currentLang={lang} onLanguageChange={onSelectLanguage} />

          {/* Cart Bag Icon with Counter */}
          <button
            id="btn-navbar-cart"
            onClick={() => {
              soundManager.playPluck();
              onOpenCart();
            }}
            className="relative p-2 rounded-full border border-neutral-300 dark:border-[#d7a9a3]/30 bg-white/70 dark:bg-[#1a0f17]/80 backdrop-blur-md text-neutral-800 dark:text-[#f5ecea] hover:border-[#d7a9a3] transition-all shadow-sm cursor-pointer"
            aria-label="Shopping Bag"
          >
            <ShoppingBag className="w-4 h-4" />
            {cartCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-[#d7a9a3] text-[#291823] font-bold text-xs flex items-center justify-center shadow-md animate-scale">
                {cartCount}
              </span>
            )}
          </button>

          {/* Mobile Menu Toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 rounded-full border border-neutral-300 dark:border-neutral-700 text-neutral-700 dark:text-neutral-300 cursor-pointer"
          >
            {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-b border-neutral-200 dark:border-neutral-800 bg-white/98 dark:bg-black/98 backdrop-blur-xl px-6 py-4 space-y-3 animate-in fade-in duration-200">
          <button
            onClick={() => {
              onNavigateTo('section-catalog');
              setMobileMenuOpen(false);
            }}
            className="block w-full text-left py-2 text-xs uppercase font-medium tracking-widest text-neutral-700 dark:text-neutral-200 hover:text-amber-500"
          >
            {t.navCatalog}
          </button>
          <button
            onClick={() => {
              onNavigateTo('section-atelier');
              setMobileMenuOpen(false);
            }}
            className="block w-full text-left py-2 text-xs uppercase font-medium tracking-widest text-neutral-700 dark:text-neutral-200 hover:text-amber-500"
          >
            {t.navAtelier}
          </button>
          <button
            onClick={() => {
              onNavigateTo('section-brands');
              setMobileMenuOpen(false);
            }}
            className="block w-full text-left py-2 text-xs uppercase font-medium tracking-widest text-neutral-700 dark:text-neutral-200 hover:text-amber-500"
          >
            {t.navAbout}
          </button>
        </div>
      )}
    </header>
  );
}
