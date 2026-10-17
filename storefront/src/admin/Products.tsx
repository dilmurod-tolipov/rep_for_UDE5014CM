import { useMemo, useRef, useState, ChangeEvent, FormEvent } from 'react';
import { Plus, Search, Pencil, Eye, EyeOff, ImagePlus } from 'lucide-react';
import { Language, Product } from '../types';
import { useProducts } from '../data/useStore';
import { deleteProduct, newProductId, saveProduct, StoreError } from '../data/store';
import { ADMIN_TEXT, BRAND_LABEL, formatSum } from './i18n';
import { Button, Card, Confirm, Sheet } from './ui';
import { SafeImage, thumbOf } from '../components/SafeImage';

const BRANDS: Product['brand'][] = ['secret_flowers', 'secret_berries', 'green_mood'];
const LANGS: Language[] = ['uz', 'ru', 'en'];

export function ProductsPage({ lang }: { lang: Language }) {
  const t = ADMIN_TEXT[lang];
  const products = useProducts(true);
  const [brand, setBrand] = useState<'all' | Product['brand']>('all');
  const [q, setQ] = useState('');
  const [editing, setEditing] = useState<Product | null>(null);
  const [error, setError] = useState('');

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    return (products ?? []).filter((p) =>
      (brand === 'all' || p.brand === brand) &&
      (!s || LANGS.some((l) => p.title[l]?.toLowerCase().includes(s)) || p.id.includes(s))
    );
  }, [products, brand, q]);

  const quickSave = (p: Product) => saveProduct(p).catch((e) => setError(e instanceof StoreError && e.code === 'storage_full' ? t.storageFull : String(e)));

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-3">
        <div>
          <h1 className="font-serif text-3xl text-white">{t.products}</h1>
          <p className="text-xs text-neutral-500 mt-0.5">{products?.length ?? 0} {t.productsCount}</p>
        </div>
        <Button variant="primary" onClick={() => setEditing(blankProduct())}><Plus className="w-4 h-4" />{t.addProduct}</Button>
      </div>

      {error && <div className="rounded-xl border border-red-500/40 bg-red-500/10 text-red-200 text-sm p-3" role="alert">{error}</div>}

      <div className="flex flex-col sm:flex-row gap-2">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-neutral-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t.search} className="w-full min-h-[44px] rounded-xl bg-white/5 border border-white/10 pl-9 pr-3 text-base sm:text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-[#d7a9a3]" />
        </div>
        <div className="flex gap-2 overflow-x-auto">
          {(['all', ...BRANDS] as const).map((b) => (
            <button key={b} onClick={() => setBrand(b)} className={`shrink-0 min-h-[40px] px-3 rounded-xl text-xs font-medium border cursor-pointer ${brand === b ? 'bg-[#d7a9a3] text-[#291823] border-[#d7a9a3]' : 'bg-white/5 text-neutral-300 border-white/10'}`}>
              {b === 'all' ? t.all : BRAND_LABEL[b]}
            </button>
          ))}
        </div>
      </div>

      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-3">
        {filtered.map((p) => (
          <Card key={p.id} className={`p-3 flex gap-3 ${p.hidden ? 'opacity-60' : ''}`}>
            <SafeImage src={thumbOf(p.images[0])} alt="" className="w-20 h-24 rounded-xl object-cover shrink-0" />
            <div className="flex-1 min-w-0 flex flex-col">
              <div className="text-[10px] uppercase tracking-wider text-neutral-500">{BRAND_LABEL[p.brand]}</div>
              <div className="text-sm text-white font-medium leading-snug line-clamp-2">{p.title[lang]}</div>
              <PriceInline product={p} onSave={quickSave} />
              <div className="mt-auto flex items-center gap-1.5 pt-2 flex-wrap">
                <button
                  onClick={() => quickSave({ ...p, inStock: p.inStock === false })}
                  className={`min-h-[32px] px-2.5 rounded-lg text-[11px] font-semibold border cursor-pointer ${p.inStock === false ? 'border-red-400/40 text-red-300 bg-red-500/10' : 'border-emerald-400/40 text-emerald-300 bg-emerald-500/10'}`}
                >
                  {p.inStock === false ? t.soldOut : t.inStock}
                </button>
                <button
                  onClick={() => quickSave({ ...p, hidden: !p.hidden })}
                  className="min-h-[32px] px-2.5 rounded-lg text-[11px] font-semibold border border-white/15 text-neutral-300 bg-white/5 inline-flex items-center gap-1 cursor-pointer"
                  aria-pressed={!p.hidden}
                >
                  {p.hidden ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  {p.hidden ? t.hidden : t.visible}
                </button>
                <button onClick={() => setEditing(p)} className="ml-auto min-h-[32px] px-2.5 rounded-lg text-[11px] font-semibold text-[#d7a9a3] hover:bg-white/5 inline-flex items-center gap-1 cursor-pointer">
                  <Pencil className="w-3.5 h-3.5" />{t.edit}
                </button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <Sheet open={!!editing} onClose={() => setEditing(null)} title={editing && products?.some((p) => p.id === editing.id) ? editing.title[lang] || t.edit : t.newProduct} wide>
        {editing && <ProductEditor key={editing.id} product={editing} lang={lang} isNew={!products?.some((p) => p.id === editing.id)} onDone={() => setEditing(null)} />}
      </Sheet>
    </div>
  );
}

function PriceInline({ product, onSave }: { product: Product; onSave: (p: Product) => void }) {
  const [value, setValue] = useState(String(product.price));
  const [editing, setEditing] = useState(false);
  if (!editing) {
    return (
      <button onClick={() => { setValue(String(product.price)); setEditing(true); }} className="text-left text-sm text-[#f5ecea] tabular-nums mt-1 hover:underline decoration-dotted cursor-pointer">
        {formatSum(product.price)}
      </button>
    );
  }
  const commit = () => {
    const n = Math.round(Number(value.replace(/\s/g, '')));
    if (Number.isFinite(n) && n > 0 && n !== product.price) onSave({ ...product, price: n });
    setEditing(false);
  };
  return (
    <input
      autoFocus
      inputMode="numeric"
      value={value}
      onChange={(e) => setValue(e.target.value.replace(/[^\d\s]/g, ''))}
      onBlur={commit}
      onKeyDown={(e) => { if (e.key === 'Enter') commit(); if (e.key === 'Escape') setEditing(false); }}
      className="mt-1 w-36 min-h-[36px] rounded-lg bg-black/40 border border-[#d7a9a3] px-2 text-base sm:text-sm text-white tabular-nums focus:outline-none"
      aria-label="Price"
    />
  );
}

function blankProduct(): Product {
  const empty = { uz: '', ru: '', en: '' };
  return {
    id: newProductId('secret_flowers'), brand: 'secret_flowers', category: 'bouquets', tags: [],
    rating: 0, reviewsCount: 0, price: 0, prepTimeMinutes: 60, dimensions: '', images: [],
    title: { ...empty }, subtitle: { ...empty }, description: { ...empty },
    composition: { uz: [], ru: [], en: [] }, careTips: { uz: [], ru: [], en: [] }, inStock: true, hidden: true
  };
}

/** Shrinks a photo in the browser to max 1000px JPEG so it fits in demo storage and loads fast on phones. */
function resizeImage(file: File, max = 1000, quality = 0.8): Promise<string> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(1, max / Math.max(img.width, img.height));
      const c = document.createElement('canvas');
      c.width = Math.round(img.width * scale);
      c.height = Math.round(img.height * scale);
      const ctx = c.getContext('2d');
      if (!ctx) { URL.revokeObjectURL(url); reject(new Error('no canvas')); return; }
      ctx.drawImage(img, 0, 0, c.width, c.height);
      URL.revokeObjectURL(url);
      resolve(c.toDataURL('image/jpeg', quality));
    };
    img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('bad image')); };
    img.src = url;
  });
}

function ProductEditor({ product, lang, isNew, onDone }: { product: Product; lang: Language; isNew: boolean; onDone: () => void }) {
  const t = ADMIN_TEXT[lang];
  const [p, setP] = useState<Product>(product);
  const [tab, setTab] = useState<Language>(lang);
  const [error, setError] = useState('');
  const [confirmDelete, setConfirmDelete] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const setText = (field: 'title' | 'subtitle' | 'description', l: Language, v: string) => setP((x) => ({ ...x, [field]: { ...x[field], [l]: v } }));
  const setList = (field: 'composition' | 'careTips', l: Language, v: string) => setP((x) => ({ ...x, [field]: { ...x[field], [l]: v.split('\n') } }));

  const onPhoto = async (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    e.target.value = '';
    if (!f) return;
    try {
      const data = await resizeImage(f);
      setP((x) => ({ ...x, images: [data] }));
    } catch {
      setError('Photo could not be read');
    }
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!p.title.uz.trim() || !p.price || !p.images.length) { setError(t.required + ': ' + [!p.title.uz.trim() && `${t.title} (UZ)`, !p.price && t.price, !p.images.length && t.photo].filter(Boolean).join(', ')); return; }
    // fill missing languages from Uzbek so the shop never shows an empty name
    const fill = (r: Record<Language, string>) => ({ uz: r.uz, ru: r.ru || r.uz, en: r.en || r.uz });
    const clean = (r: Record<Language, string[]>) => ({ uz: r.uz.filter((s) => s.trim()), ru: r.ru.filter((s) => s.trim()), en: r.en.filter((s) => s.trim()) });
    const id = isNew ? newProductId(p.brand) : p.id;
    try {
      await saveProduct({ ...p, id, title: fill(p.title), subtitle: fill(p.subtitle), description: fill(p.description), composition: clean(p.composition), careTips: clean(p.careTips) });
      onDone();
    } catch (err) {
      setError(err instanceof StoreError && err.code === 'storage_full' ? t.storageFull : String(err));
    }
  };

  const field = 'w-full min-h-[44px] rounded-xl bg-black/30 border border-white/15 px-3 text-base sm:text-sm text-white focus:outline-none focus:border-[#d7a9a3]';
  const lbl = 'block text-xs text-neutral-400 mb-1.5';

  return (
    <form onSubmit={submit} className="space-y-5">
      <div className="flex gap-4 items-start">
        <div className="shrink-0">
          <SafeImage src={p.images[0] ?? ''} alt="" className="w-28 h-32 sm:w-36 sm:h-44 rounded-2xl object-cover border border-white/10" />
          <input ref={fileRef} type="file" accept="image/*" onChange={onPhoto} className="hidden" />
          <Button onClick={() => fileRef.current?.click()} className="mt-2 w-full text-xs"><ImagePlus className="w-4 h-4" />{p.images.length ? t.changePhoto : t.photo}</Button>
          <p className="text-[10px] text-neutral-500 mt-1 text-center">{t.photoHint}</p>
        </div>
        <div className="flex-1 grid gap-3">
          <div>
            <label className={lbl}>{t.brand}</label>
            <select value={p.brand} onChange={(e) => setP({ ...p, brand: e.target.value as Product['brand'] })} className={field}>
              {BRANDS.map((b) => <option key={b} value={b}>{BRAND_LABEL[b]}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={lbl}>{t.price} (so‘m)</label>
              <input inputMode="numeric" value={p.price || ''} onChange={(e) => setP({ ...p, price: Number(e.target.value.replace(/\D/g, '')) })} className={field + ' tabular-nums'} />
            </div>
            <div>
              <label className={lbl}>{t.prepTime}</label>
              <input inputMode="numeric" value={p.prepTimeMinutes || ''} onChange={(e) => setP({ ...p, prepTimeMinutes: Number(e.target.value.replace(/\D/g, '')) })} className={field + ' tabular-nums'} />
            </div>
          </div>
          <div className="flex flex-wrap gap-4 text-sm text-neutral-200">
            <label className="inline-flex items-center gap-2 min-h-[36px]"><input type="checkbox" checked={p.inStock !== false} onChange={(e) => setP({ ...p, inStock: e.target.checked })} className="w-4 h-4 accent-[#d7a9a3]" />{t.inStock}</label>
            <label className="inline-flex items-center gap-2 min-h-[36px]"><input type="checkbox" checked={!p.hidden} onChange={(e) => setP({ ...p, hidden: !e.target.checked })} className="w-4 h-4 accent-[#d7a9a3]" />{t.showInShop}</label>
          </div>
        </div>
      </div>

      <div>
        <div className="flex gap-1 mb-3" role="tablist">
          {LANGS.map((l) => (
            <button type="button" key={l} role="tab" aria-selected={tab === l} onClick={() => setTab(l)} className={`min-h-[36px] px-4 rounded-lg text-xs font-bold cursor-pointer ${tab === l ? 'bg-[#d7a9a3] text-[#291823]' : 'bg-white/5 text-neutral-400'}`}>
              {l.toUpperCase()}{l === 'uz' ? ' *' : ''}
            </button>
          ))}
        </div>
        <div className="grid gap-3">
          <div><label className={lbl}>{t.title}</label><input value={p.title[tab]} onChange={(e) => setText('title', tab, e.target.value)} className={field} /></div>
          <div><label className={lbl}>{t.subtitle}</label><input value={p.subtitle[tab]} onChange={(e) => setText('subtitle', tab, e.target.value)} className={field} /></div>
          <div><label className={lbl}>{t.description}</label><textarea rows={3} value={p.description[tab]} onChange={(e) => setText('description', tab, e.target.value)} className={field + ' py-2'} /></div>
          <div><label className={lbl}>{t.composition}</label><textarea rows={3} value={p.composition[tab].join('\n')} onChange={(e) => setList('composition', tab, e.target.value)} className={field + ' py-2'} /></div>
          <div><label className={lbl}>{t.careTips}</label><textarea rows={3} value={p.careTips[tab].join('\n')} onChange={(e) => setList('careTips', tab, e.target.value)} className={field + ' py-2'} /></div>
        </div>
      </div>

      {error && <div className="rounded-xl border border-red-500/40 bg-red-500/10 text-red-200 text-sm p-3" role="alert">{error}</div>}

      <div className="flex gap-2 justify-between sticky bottom-0 bg-[#120b10] py-3 -mx-5 px-5 border-t border-white/10">
        {!isNew ? <Button variant="danger" onClick={() => setConfirmDelete(true)}>{t.delete}</Button> : <span />}
        <div className="flex gap-2">
          <Button onClick={onDone}>{t.cancel}</Button>
          <Button type="submit" variant="primary">{t.save}</Button>
        </div>
      </div>

      <Confirm open={confirmDelete} text={t.deleteConfirm} confirmLabel={t.delete} cancelLabel={t.cancel} danger onCancel={() => setConfirmDelete(false)} onConfirm={() => { deleteProduct(p.id).then(onDone); }} />
    </form>
  );
}
