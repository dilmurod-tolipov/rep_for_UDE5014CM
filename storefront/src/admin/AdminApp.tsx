import { useEffect, useState, FormEvent } from 'react';
import { LayoutDashboard, ShoppingBag, Flower2, LogOut, ExternalLink, RotateCcw } from 'lucide-react';
import { Language } from '../types';
import { ADMIN_TEXT } from './i18n';
import { Button, Confirm } from './ui';
import { Dashboard } from './Dashboard';
import { OrdersPage } from './Orders';
import { ProductsPage } from './Products';
import { resetDemoData } from '../data/store';
import { useOrders } from '../data/useStore';

type Tab = 'dashboard' | 'orders' | 'products';
const SESSION_KEY = 'secret.admin.session';
const LANG_KEY = 'secret.admin.lang';
/** DEMO ONLY: a password in the page code is not security. Replace with real sign-in (e.g. Firebase Auth / Identity Platform) on GCP. */
const DEMO_PASSWORD = 'secret';

function safeGet(store: Storage | undefined, key: string) {
  try { return store?.getItem(key) ?? null; } catch { return null; }
}
function safeSet(store: Storage | undefined, key: string, v: string | null) {
  try { if (v === null) store?.removeItem(key); else store?.setItem(key, v); } catch { /* ignore */ }
}

export default function AdminApp() {
  const [lang, setLang] = useState<Language>(() => (safeGet(window.localStorage, LANG_KEY) as Language) || 'uz');
  const [signedIn, setSignedIn] = useState(() => safeGet(window.sessionStorage, SESSION_KEY) === '1');
  const [tab, setTab] = useState<Tab>(() => (location.hash.replace('#', '') as Tab) || 'dashboard');
  const [confirmReset, setConfirmReset] = useState(false);
  const t = ADMIN_TEXT[lang];
  const orders = useOrders();
  const newCount = orders?.filter((o) => o.status === 'new').length ?? 0;

  useEffect(() => {
    document.title = `${t.admin} · Secret`;
    document.documentElement.classList.add('dark');
    safeSet(window.localStorage, LANG_KEY, lang);
  }, [lang, t.admin]);

  useEffect(() => {
    if (location.hash !== `#${tab}`) history.replaceState(null, '', `#${tab}`);
    window.scrollTo(0, 0);
  }, [tab]);

  if (!signedIn) return <Login lang={lang} setLang={setLang} onSignedIn={() => { safeSet(window.sessionStorage, SESSION_KEY, '1'); setSignedIn(true); }} />;

  const nav: { id: Tab; label: string; icon: typeof LayoutDashboard; badge?: number }[] = [
    { id: 'dashboard', label: t.dashboard, icon: LayoutDashboard },
    { id: 'orders', label: t.orders, icon: ShoppingBag, badge: newCount },
    { id: 'products', label: t.products, icon: Flower2 }
  ];

  return (
    <div className="min-h-screen bg-[#0c060b] text-neutral-100 font-sans">
      {/* Top bar */}
      <header className="sticky top-0 z-30 bg-[#0c060b]/95 border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center gap-3">
          <img src="/logo-circle.webp" alt="" className="w-8 h-8 rounded-full" />
          <div className="font-serif text-lg tracking-[0.2em] text-[#d7a9a3]">SECRET</div>
          <span className="hidden sm:inline text-xs text-neutral-500">{t.admin}</span>
          <div className="ml-auto flex items-center gap-1.5">
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value as Language)}
              className="bg-white/5 border border-white/10 rounded-lg text-xs px-2 min-h-[36px] text-neutral-200"
              aria-label="Language"
            >
              <option value="uz">UZ</option><option value="ru">RU</option><option value="en">EN</option>
            </select>
            <a href="/" className="hidden sm:inline-flex items-center gap-1 text-xs text-neutral-400 hover:text-white px-2 min-h-[36px]"><ExternalLink className="w-3.5 h-3.5" />{t.viewShop}</a>
            <button onClick={() => setConfirmReset(true)} className="inline-flex items-center gap-1 text-xs text-neutral-400 hover:text-white px-2 min-h-[36px] cursor-pointer" title={t.resetDemo}>
              <RotateCcw className="w-3.5 h-3.5" /><span className="hidden md:inline">{t.resetDemo}</span>
            </button>
            <button onClick={() => { safeSet(window.sessionStorage, SESSION_KEY, null); setSignedIn(false); }} className="inline-flex items-center gap-1 text-xs text-neutral-400 hover:text-white px-2 min-h-[36px] cursor-pointer" title={t.signOut}>
              <LogOut className="w-3.5 h-3.5" /><span className="hidden md:inline">{t.signOut}</span>
            </button>
          </div>
        </div>
        <div className="bg-amber-400 text-neutral-950 text-[11px] font-semibold text-center px-3 py-1">{t.demoData}</div>
      </header>

      <div className="max-w-7xl mx-auto md:flex">
        {/* Side nav (tablet/desktop) */}
        <nav className="hidden md:block w-56 shrink-0 p-4 sticky top-[82px] self-start">
          {nav.map((n) => (
            <button
              key={n.id}
              onClick={() => setTab(n.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 mb-1 rounded-xl text-sm cursor-pointer ${tab === n.id ? 'bg-[#d7a9a3]/15 text-[#f5ecea] font-semibold' : 'text-neutral-400 hover:bg-white/5'}`}
            >
              <n.icon className="w-4 h-4" />
              <span className="flex-1 text-left">{n.label}</span>
              {!!n.badge && <span className="text-[10px] font-bold bg-amber-400 text-neutral-950 rounded-full px-1.5 py-0.5">{n.badge}</span>}
            </button>
          ))}
        </nav>

        <main className="flex-1 min-w-0 p-4 md:p-6 pb-28 md:pb-10">
          {tab === 'dashboard' && <Dashboard lang={lang} onOpenOrders={() => setTab('orders')} />}
          {tab === 'orders' && <OrdersPage lang={lang} />}
          {tab === 'products' && <ProductsPage lang={lang} />}
        </main>
      </div>

      {/* Bottom tabs (phones) */}
      <nav className="md:hidden fixed bottom-0 inset-x-0 z-30 bg-[#120b10]/97 border-t border-white/10 grid grid-cols-3 pb-[env(safe-area-inset-bottom)]">
        {nav.map((n) => (
          <button key={n.id} onClick={() => setTab(n.id)} className={`relative flex flex-col items-center gap-0.5 py-2.5 text-[11px] cursor-pointer ${tab === n.id ? 'text-[#d7a9a3] font-semibold' : 'text-neutral-400'}`}>
            <n.icon className="w-5 h-5" />
            {n.label}
            {!!n.badge && <span className="absolute top-1.5 left-1/2 ml-2 text-[10px] font-bold bg-amber-400 text-neutral-950 rounded-full px-1.5">{n.badge}</span>}
          </button>
        ))}
      </nav>

      <Confirm
        open={confirmReset}
        text={t.resetConfirm}
        confirmLabel={t.resetDemo}
        cancelLabel={t.cancel}
        danger
        onCancel={() => setConfirmReset(false)}
        onConfirm={() => { resetDemoData(); setConfirmReset(false); }}
      />
    </div>
  );
}

function Login({ lang, setLang, onSignedIn }: { lang: Language; setLang: (l: Language) => void; onSignedIn: () => void }) {
  const t = ADMIN_TEXT[lang];
  const [pw, setPw] = useState('');
  const [error, setError] = useState(false);
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (pw.trim() === DEMO_PASSWORD) onSignedIn();
    else setError(true);
  };
  return (
    <div className="min-h-screen bg-[#0c060b] flex items-center justify-center p-4 font-sans">
      <form onSubmit={submit} className="w-full max-w-sm rounded-3xl border border-white/10 bg-[#171016] p-7 shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <img src="/logo-circle.webp" alt="" className="w-10 h-10 rounded-full" />
            <div>
              <div className="font-serif text-xl tracking-[0.2em] text-[#d7a9a3]">SECRET</div>
              <div className="text-xs text-neutral-500">{t.admin}</div>
            </div>
          </div>
          <select value={lang} onChange={(e) => setLang(e.target.value as Language)} className="bg-white/5 border border-white/10 rounded-lg text-xs px-2 min-h-[36px] text-neutral-200" aria-label="Language">
            <option value="uz">UZ</option><option value="ru">RU</option><option value="en">EN</option>
          </select>
        </div>
        <label className="block text-xs text-neutral-400 mb-1.5" htmlFor="admin-pw">{t.password}</label>
        <input
          id="admin-pw"
          type="password"
          autoComplete="current-password"
          value={pw}
          onChange={(e) => { setPw(e.target.value); setError(false); }}
          className="w-full min-h-[44px] rounded-xl bg-black/30 border border-white/15 px-3 text-base text-white focus:outline-none focus:border-[#d7a9a3]"
        />
        {error && <p className="text-xs text-red-300 mt-2" role="alert">{t.wrongPassword}</p>}
        <Button type="submit" variant="primary" className="w-full mt-4">{t.signIn}</Button>
        <p className="text-[11px] text-amber-300/90 mt-4 leading-relaxed">{t.demoLoginHint}</p>
      </form>
    </div>
  );
}
