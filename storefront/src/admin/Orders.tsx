import { useMemo, useState } from 'react';
import { Phone, Search, Gift, ChevronRight } from 'lucide-react';
import { Language, Order, OrderStatus } from '../types';
import { useOrders } from '../data/useStore';
import { updateOrder } from '../data/store';
import { ADMIN_TEXT, BRAND_LABEL, METHOD_LABEL, STATUS_FLOW, STATUS_LABEL, formatDateTime, formatSum } from './i18n';
import { Button, Card, Sheet, StatusBadge } from './ui';
import { SafeImage, thumbOf } from '../components/SafeImage';

const FILTERS: (OrderStatus | 'all' | 'open')[] = ['open', 'new', 'confirmed', 'assembling', 'in_transit', 'delivered', 'cancelled', 'all'];
const isOpen = (o: Order) => o.status !== 'delivered' && o.status !== 'cancelled';

export function OrdersPage({ lang }: { lang: Language }) {
  const t = ADMIN_TEXT[lang];
  const orders = useOrders();
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>('open');
  const [q, setQ] = useState('');
  const [openId, setOpenId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    if (!orders) return [];
    const s = q.trim().toLowerCase();
    return orders.filter((o) => {
      const byStatus = filter === 'all' || (filter === 'open' ? isOpen(o) : o.status === filter);
      const bySearch = !s || [o.orderNumber, o.customer.name, o.customer.phone, o.recipient.name].some((v) => v?.toLowerCase().includes(s));
      return byStatus && bySearch;
    });
  }, [orders, filter, q]);

  const countFor = (f: (typeof FILTERS)[number]) =>
    !orders ? 0 : f === 'all' ? orders.length : f === 'open' ? orders.filter(isOpen).length : orders.filter((o) => o.status === f).length;
  const label = (f: (typeof FILTERS)[number]) => (f === 'all' ? t.all : f === 'open' ? t.openOrders : STATUS_LABEL[lang][f]);
  const current = orders?.find((o) => o.id === openId) ?? null;

  return (
    <div className="space-y-4">
      <h1 className="font-serif text-3xl text-white">{t.orders}</h1>

      <div className="relative">
        <Search className="w-4 h-4 text-neutral-500 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t.searchOrders}
          className="w-full min-h-[44px] rounded-xl bg-white/5 border border-white/10 pl-9 pr-3 text-base sm:text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-[#d7a9a3]"
        />
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1 -mx-4 px-4 sm:mx-0 sm:px-0 sm:flex-wrap">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`shrink-0 min-h-[36px] px-3 rounded-full text-xs font-medium border cursor-pointer ${filter === f ? 'bg-[#d7a9a3] text-[#291823] border-[#d7a9a3]' : 'bg-white/5 text-neutral-300 border-white/10 hover:bg-white/10'}`}
          >
            {label(f)} <span className="opacity-70 tabular-nums">{countFor(f)}</span>
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <Card className="p-8 text-center text-sm text-neutral-500">{t.noOrders}</Card>
      ) : (
        <div className="grid gap-2.5">
          {filtered.map((o) => (
            <button key={o.id} onClick={() => setOpenId(o.id)} className="text-left cursor-pointer">
              <Card className="p-4 hover:border-[#d7a9a3]/40 transition-colors flex items-center gap-3">
                <SafeImage src={thumbOf(o.items[0]?.productImage ?? '')} alt="" className="w-12 h-12 rounded-xl object-cover shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-white text-sm">#{o.orderNumber}</span>
                    <StatusBadge status={o.status} lang={lang} />
                    {o.isDemo && <span className="text-[10px] uppercase tracking-wider text-neutral-500">{t.demoTag}</span>}
                  </div>
                  <div className="text-xs text-neutral-400 truncate mt-0.5">
                    {o.customer.name} · {o.items.map((i) => i.productTitle[lang]).join(', ')}
                  </div>
                  <div className="text-[11px] text-neutral-500 mt-0.5">{formatDateTime(o.createdAt, lang)} · {o.delivery.district}</div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-sm font-semibold text-white tabular-nums whitespace-nowrap">{formatSum(o.total)}</div>
                  <ChevronRight className="w-4 h-4 text-neutral-500 ml-auto mt-1" />
                </div>
              </Card>
            </button>
          ))}
        </div>
      )}

      <Sheet open={!!current} onClose={() => setOpenId(null)} title={current ? `#${current.orderNumber}` : ''}>
        {current && <OrderDetail key={current.id} order={current} lang={lang} />}
      </Sheet>
    </div>
  );
}

function OrderDetail({ order, lang }: { order: Order; lang: Language }) {
  const t = ADMIN_TEXT[lang];
  const [note, setNote] = useState(order.adminNote ?? '');
  const [noteSaved, setNoteSaved] = useState(false);
  const idx = STATUS_FLOW.indexOf(order.status);
  const next = idx >= 0 && idx < STATUS_FLOW.length - 1 ? STATUS_FLOW[idx + 1] : null;
  const setStatus = (status: OrderStatus) => updateOrder(order.id, { status });
  const payLabel = order.payment.status === 'paid' ? t.paid : order.payment.status === 'cash_on_delivery' ? t.cod : t.pending;

  return (
    <div className="space-y-5 text-sm">
      <div className="flex items-center gap-2 flex-wrap">
        <StatusBadge status={order.status} lang={lang} />
        <span className="text-xs text-neutral-400">{formatDateTime(order.createdAt, lang)}</span>
        <span className="text-xs text-neutral-500">· {BRAND_LABEL[order.brand] ?? order.brand}</span>
      </div>

      {/* Status progress */}
      <ol className="flex items-center gap-1" aria-label="Status">
        {STATUS_FLOW.map((s, i) => (
          <li key={s} className="flex-1">
            <div className={`h-1.5 rounded-full ${order.status !== 'cancelled' && i <= idx ? 'bg-[#d7a9a3]' : 'bg-white/10'}`} />
            <div className={`mt-1 text-[10px] truncate ${i === idx ? 'text-white font-semibold' : 'text-neutral-500'}`}>{STATUS_LABEL[lang][s]}</div>
          </li>
        ))}
      </ol>

      <div className="flex flex-wrap gap-2">
        {order.status === 'cancelled' ? (
          <Button variant="primary" onClick={() => setStatus('new')}>{t.reopen}</Button>
        ) : (
          <>
            {next && <Button variant="primary" onClick={() => setStatus(next)}>{t.nextStep}: {STATUS_LABEL[lang][next]}</Button>}
            {order.status !== 'delivered' && <Button variant="danger" onClick={() => setStatus('cancelled')}>{t.cancelOrder}</Button>}
          </>
        )}
      </div>

      <section>
        <h3 className="text-xs uppercase tracking-wider text-neutral-400 mb-2">{t.items}</h3>
        <ul className="space-y-2">
          {order.items.map((i, k) => (
            <li key={k} className="flex items-center gap-3">
              <SafeImage src={thumbOf(i.productImage)} alt="" className="w-11 h-11 rounded-lg object-cover shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-neutral-100 truncate">{i.productTitle[lang]}</div>
                <div className="text-xs text-neutral-400">{i.quantity} × {formatSum(i.price)}</div>
                {i.cardMessage && <div className="text-xs text-[#d7a9a3] mt-0.5">“{i.cardMessage}”</div>}
              </div>
              <div className="tabular-nums text-neutral-100 whitespace-nowrap">{formatSum(i.price * i.quantity)}</div>
            </li>
          ))}
        </ul>
        <div className="mt-3 pt-3 border-t border-white/10 space-y-1 text-xs">
          <Row k={t.subtotal} v={formatSum(order.subtotal)} />
          <Row k={t.deliveryFee} v={formatSum(order.deliveryFee)} />
          <div className="flex justify-between text-sm font-semibold text-white pt-1"><span>{t.total}</span><span className="tabular-nums">{formatSum(order.total)}</span></div>
        </div>
      </section>

      <div className="grid sm:grid-cols-2 gap-3">
        <Card className="p-4">
          <h3 className="text-xs uppercase tracking-wider text-neutral-400 mb-2">{t.customer}</h3>
          <div className="text-neutral-100">{order.customer.name}</div>
          <PhoneLink phone={order.customer.phone} label={t.call} />
        </Card>
        <Card className="p-4">
          <h3 className="text-xs uppercase tracking-wider text-neutral-400 mb-2">{t.recipient}</h3>
          <div className="text-neutral-100">{order.recipient.name}</div>
          <PhoneLink phone={order.recipient.phone} label={t.call} />
          {order.recipient.isSurprise && <div className="mt-2 inline-flex items-center gap-1 text-xs text-[#d7a9a3]"><Gift className="w-3.5 h-3.5" />{t.surprise}</div>}
        </Card>
        <Card className="p-4">
          <h3 className="text-xs uppercase tracking-wider text-neutral-400 mb-2">{t.delivery}</h3>
          <div className="text-neutral-100">{order.delivery.district}</div>
          <div className="text-neutral-300 text-xs mt-0.5">{[order.delivery.address, order.delivery.apartment, order.delivery.landmark].filter(Boolean).join(', ')}</div>
          <div className="text-neutral-400 text-xs mt-1">{order.delivery.date} · {order.delivery.timeSlot}</div>
        </Card>
        <Card className="p-4">
          <h3 className="text-xs uppercase tracking-wider text-neutral-400 mb-2">{t.payment}</h3>
          <div className="text-neutral-100">{METHOD_LABEL[order.payment.method]}</div>
          <div className="text-xs text-neutral-300 mt-0.5">{payLabel}{order.payment.transactionId ? ` · ${order.payment.transactionId}` : ''}</div>
        </Card>
      </div>

      {(order.cardMessage || order.notes) && (
        <Card className="p-4 text-xs text-neutral-300 space-y-1">
          {order.cardMessage && <div><span className="text-neutral-500">{t.cardMessage}: </span>“{order.cardMessage}”</div>}
          {order.notes && <div>{order.notes}</div>}
        </Card>
      )}

      <section>
        <label htmlFor="admin-note" className="text-xs uppercase tracking-wider text-neutral-400">{t.note}</label>
        <textarea
          id="admin-note"
          value={note}
          onChange={(e) => { setNote(e.target.value); setNoteSaved(false); }}
          rows={3}
          className="mt-2 w-full rounded-xl bg-black/30 border border-white/15 p-3 text-base sm:text-sm text-white focus:outline-none focus:border-[#d7a9a3]"
        />
        <div className="flex items-center gap-3 mt-2">
          <Button onClick={() => updateOrder(order.id, { adminNote: note }).then(() => setNoteSaved(true))}>{t.saveNote}</Button>
          {noteSaved && <span className="text-xs text-emerald-300">{t.saved}</span>}
        </div>
      </section>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return <div className="flex justify-between text-neutral-400"><span>{k}</span><span className="tabular-nums text-neutral-200">{v}</span></div>;
}

function PhoneLink({ phone, label }: { phone: string; label: string }) {
  return (
    <a href={`tel:${phone.replace(/\s/g, '')}`} className="mt-1 inline-flex items-center gap-1.5 text-xs text-[#d7a9a3] min-h-[32px]">
      <Phone className="w-3.5 h-3.5" /> {phone} <span className="sr-only">{label}</span>
    </a>
  );
}
