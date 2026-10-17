import { Search, ArrowUpDown, LayoutGrid } from 'lucide-react';
import { Language, Product } from '../types';
import { ProductCard } from './ProductCard';
import { SafeImage } from './SafeImage';
import { soundManager } from '../utils/audio';

export type BrandKey = Product['brand'];
export type CatalogFilter = 'all' | BrandKey;
export type SortKey = 'featured' | 'price_asc' | 'price_desc';

/** The three shop categories, in the order they appear on the page. */
export const CATEGORIES: {
  key: BrandKey;
  name: string;
  cover: string;
  accent: string; // text accent
  ring: string; // selected ring
  tagline: Record<Language, string>;
}[] = [
  {
    key: 'secret_flowers',
    name: 'Secret Flowers',
    cover: '/images/flowers/thumb/fl-02.jpg',
    accent: 'text-rose-500 dark:text-rose-300',
    ring: 'ring-rose-400',
    tagline: {
      uz: 'Gortenziya, orxideya va atirgullardan mualliflik guldastalari',
      ru: 'Авторские букеты из гортензий, орхидей и роз',
      en: 'Signature bouquets of hydrangeas, orchids and roses'
    }
  },
  {
    key: 'green_mood',
    name: 'Green Mood',
    cover: '/images/plants/thumb/gm-04.jpg',
    accent: 'text-emerald-600 dark:text-emerald-300',
    ring: 'ring-emerald-400',
    tagline: {
      uz: 'Uy va ofis uchun xona o‘simliklari',
      ru: 'Комнатные растения для дома и офиса',
      en: 'Houseplants for home and office'
    }
  },
  {
    key: 'secret_berries',
    name: 'Secret Berries',
    cover: '/images/berries/thumb/sb-03.jpg',
    accent: 'text-amber-600 dark:text-amber-300',
    ring: 'ring-amber-400',
    tagline: {
      uz: 'Shokoladdagi qulupnaylar, sovg‘a qutilarida',
      ru: 'Клубника в шоколаде в подарочных коробках',
      en: 'Chocolate-covered strawberries in gift boxes'
    }
  }
];

const TXT: Record<Language, Record<string, string>> = {
  uz: { all: 'Hammasi', search: 'Guldasta, qulupnay, o‘simlik…', sort: 'Saralash', featured: 'Tavsiya', priceAsc: 'Arzonroq', priceDesc: 'Qimmatroq', items: 'ta mahsulot', none: 'Hech narsa topilmadi', reset: 'Filtrni tozalash', showAll: 'Barcha toifalar' },
  ru: { all: 'Все', search: 'Букеты, клубника, растения…', sort: 'Сортировка', featured: 'Рекомендуем', priceAsc: 'Сначала дешевле', priceDesc: 'Сначала дороже', items: 'товаров', none: 'Ничего не найдено', reset: 'Сбросить фильтр', showAll: 'Все категории' },
  en: { all: 'All', search: 'Bouquets, strawberries, plants…', sort: 'Sort', featured: 'Featured', priceAsc: 'Price: low to high', priceDesc: 'Price: high to low', items: 'items', none: 'Nothing found', reset: 'Clear filters', showAll: 'All categories' }
};

interface Props {
  lang: Language;
  heading: string;
  subheading: string;
  products: Product[]; // already search-filtered and sorted, all categories
  totals: Record<BrandKey, number>; // counts before search, for the category cards
  selected: CatalogFilter;
  onSelect: (f: CatalogFilter) => void;
  searchQuery: string;
  onSearch: (q: string) => void;
  sortBy: SortKey;
  onSort: (s: SortKey) => void;
  onQuickView: (p: Product) => void;
  onAddToCart: (p: Product) => void;
}

export function CatalogSections(props: Props) {
  const { lang, selected, onSelect, products, totals } = props;
  const t = TXT[lang];
  const visibleCats = CATEGORIES.filter((c) => selected === 'all' || c.key === selected);
  const nothing = visibleCats.every((c) => !products.some((p) => p.brand === c.key));

  const pick = (key: CatalogFilter) => {
    soundManager.playTick();
    onSelect(selected === key ? 'all' : key);
    document.getElementById('catalog-top')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <section id="section-catalog" className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto scroll-mt-20">
      <div id="catalog-top" className="scroll-mt-24" />
      {/* Heading */}
      <div className="mb-8">
        <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-light text-neutral-900 dark:text-white">{props.heading}</h2>
        <p className="text-neutral-500 dark:text-neutral-400 text-xs sm:text-sm font-light mt-1">{props.subheading}</p>
      </div>

      {/* The three categories, as large photo cards (they also work as filters) */}
      <div className="grid grid-cols-3 gap-2.5 sm:gap-5 mb-8" role="tablist" aria-label="Categories">
        {CATEGORIES.map((c) => {
          const active = selected === c.key;
          return (
            <button
              key={c.key}
              role="tab"
              aria-selected={active}
              onClick={() => pick(c.key)}
              className={`group relative overflow-hidden rounded-2xl sm:rounded-3xl text-left aspect-[3/4] sm:aspect-[4/3] cursor-pointer transition-all duration-300 ${
                active ? `ring-2 ${c.ring} ring-offset-2 ring-offset-white dark:ring-offset-[#0c060b]` : selected !== 'all' ? 'opacity-55 hover:opacity-90' : ''
              }`}
            >
              <SafeImage src={c.cover} alt={c.name} loading="lazy" className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/35 to-black/5" />
              <div className="absolute inset-x-0 bottom-0 p-2.5 sm:p-5">
                <div className="font-serif text-white text-sm sm:text-2xl lg:text-3xl leading-tight">{c.name}</div>
                <div className="hidden sm:block text-white/80 text-xs mt-1 line-clamp-2">{c.tagline[lang]}</div>
                <div className="text-white/70 text-xs sm:text-xs mt-1 tabular-nums">{totals[c.key]} {t.items}</div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Search + sort + "all" */}
      <div className="flex flex-col sm:flex-row gap-3 sm:items-center justify-between mb-10 pb-5 border-b border-neutral-200 dark:border-neutral-800">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-neutral-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="search"
            value={props.searchQuery}
            onChange={(e) => props.onSearch(e.target.value)}
            placeholder={t.search}
            className="w-full text-base sm:text-sm pl-10 pr-4 min-h-[44px] rounded-full border border-neutral-300 dark:border-neutral-700 bg-white/70 dark:bg-neutral-900/70 text-neutral-900 dark:text-white placeholder-neutral-400 focus:outline-none focus:border-[#d7a9a3]"
          />
        </div>
        <div className="flex items-center gap-2">
          {selected !== 'all' && (
            <button onClick={() => pick('all')} className="inline-flex items-center gap-1.5 min-h-[40px] px-4 rounded-full text-xs font-medium bg-neutral-100 dark:bg-[#1a0f17] text-neutral-700 dark:text-[#d7a9a3] cursor-pointer">
              <LayoutGrid className="w-3.5 h-3.5" /> {t.showAll}
            </button>
          )}
          <label className="inline-flex items-center gap-1.5 text-xs text-neutral-500">
            <ArrowUpDown className="w-3.5 h-3.5" />
            <span className="sr-only">{t.sort}</span>
            <select
              value={props.sortBy}
              onChange={(e) => props.onSort(e.target.value as SortKey)}
              className="min-h-[40px] text-xs px-3 rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-900 text-neutral-800 dark:text-neutral-200 focus:outline-none"
            >
              <option value="featured">{t.featured}</option>
              <option value="price_asc">{t.priceAsc}</option>
              <option value="price_desc">{t.priceDesc}</option>
            </select>
          </label>
        </div>
      </div>

      {nothing && (
        <div className="text-center py-16 text-neutral-400">
          <p className="text-sm">{t.none}</p>
          <button onClick={() => { props.onSearch(''); onSelect('all'); }} className="mt-4 min-h-[40px] px-4 rounded-full bg-neutral-200 dark:bg-neutral-800 text-xs font-medium cursor-pointer">{t.reset}</button>
        </div>
      )}

      {/* One section per category */}
      <div className="space-y-16">
        {visibleCats.map((c) => {
          const items = products.filter((p) => p.brand === c.key);
          if (!items.length) return null;
          return (
            <div key={c.key} id={`catalog-${c.key}`} className="scroll-mt-24">
              <div className="flex items-end justify-between gap-4 mb-6">
                <div className="flex items-center gap-3 min-w-0">
                  <SafeImage src={c.cover} alt="" className="w-12 h-12 sm:w-14 sm:h-14 rounded-2xl object-cover shrink-0" />
                  <div className="min-w-0">
                    <h3 className={`font-serif text-2xl sm:text-3xl ${c.accent}`}>{c.name}</h3>
                    <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 truncate">{c.tagline[lang]}</p>
                  </div>
                </div>
                <span className="shrink-0 text-xs tabular-nums text-neutral-400">{items.length} {t.items}</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 sm:gap-8">
                {items.map((p) => (
                  <ProductCard key={p.id} product={p} lang={lang} onQuickView={props.onQuickView} onAddToCart={props.onAddToCart} />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
