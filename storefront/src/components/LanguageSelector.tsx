import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check } from 'lucide-react';
import { Language } from '../types';
import { soundManager } from '../utils/audio';

interface LanguageSelectorProps {
  currentLang: Language;
  onLanguageChange: (lang: Language) => void;
}

const LANGUAGES: { code: Language; label: string }[] = [
  { code: 'uz', label: 'O‘zbekcha' },
  { code: 'ru', label: 'Русский' },
  { code: 'en', label: 'English' }
];

export function LanguageSelector({ currentLang, onLanguageChange }: LanguageSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const activeOption = LANGUAGES.find((l) => l.code === currentLang) || LANGUAGES[0];

  return (
    <div className="relative" ref={containerRef}>
      <button
        id="btn-language-selector"
        onClick={() => {
          soundManager.playTick();
          setIsOpen(!isOpen);
        }}
        className="flex items-center gap-1.5 px-3.5 min-h-[40px] rounded-full border border-neutral-300 dark:border-neutral-700 bg-white/70 dark:bg-neutral-900/70 backdrop-blur-md text-xs font-medium text-neutral-800 dark:text-neutral-200 hover:border-amber-400/50 transition-all shadow-sm cursor-pointer"
        aria-label="Select language"
      >
        <span className="uppercase font-semibold tracking-wider text-[11px]">{activeOption.code}</span>
        <ChevronDown className={`w-3 h-3 text-neutral-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-36 py-1 bg-white/95 dark:bg-neutral-900/95 backdrop-blur-xl rounded-xl border border-neutral-200 dark:border-neutral-800 shadow-xl z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              id={`btn-lang-${lang.code}`}
              onClick={() => {
                soundManager.playChime(750);
                onLanguageChange(lang.code);
                setIsOpen(false);
              }}
              className={`w-full flex items-center justify-between px-3 py-2.5 text-sm transition-colors text-left cursor-pointer ${
                currentLang === lang.code
                  ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 font-semibold'
                  : 'text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800'
              }`}
            >
              <span>{lang.label}</span>
              {currentLang === lang.code && <Check className="w-3.5 h-3.5 text-amber-500" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
