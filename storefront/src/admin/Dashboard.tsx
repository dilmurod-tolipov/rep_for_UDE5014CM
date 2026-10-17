import { useEffect, useMemo, useRef, useState, PointerEvent as RPointerEvent } from 'react';
import { ArrowDownRight, ArrowUpRight, ArrowRight, Minus, CircleDot, BadgeCheck, Package, Truck } from 'lucide-react';
import { Language, Order, OrderStatus, PaymentMethod } from '../types';
import { useOrders, useProducts } from '../data/useStore';
import { ADMIN_TEXT, BRAND_LABEL, METHOD_LABEL, STATUS_LABEL, dayKey, formatDateTime, formatShort, formatSum } from './i18n';
import { Card, StatusBadge } from './ui';
import { SafeImage, thumbOf } from '../components/SafeImage';

/* ------------------------------------------------------------------ colours
   Validated with the dataviz palette checker on the admin surface #171016:
   - ACCENT: single-series marks (revenue line, bars).
   - BRAND: three categorical hues, all-pairs colour-blind safe (worst CVD ΔE 13.2);
     brand names are always printed next to the colour, never colour alone. */
const ACCENT = '#c96a62';
const MUTED = '#7d6f78'; // de-emphasis, still 3.9:1 on the surface
const BRAND_COLOR: Record<string, string> = { secret_flowers: '#d55181', green_mood: '#3987e5', secret_berries: '#c98500' };
const BRANDS = ['secret_flowers', 'green_mood', 'secret_berries'] as const;

type Period = 'today' | '7d' | '14d';

const D: Record<Language, Record<string, string>> = {
  uz: { today: 'Bugun', d7: '7 kun', d14: '14 kun', revenue: 'Tushum', vsYesterday: 'kechagiga nisbatan', vsPrev: 'oldingi davrga nisbatan', orders: 'Buyurtmalar', avg: 'O‘rtacha chek', items: 'Sotilgan mahsulot', cancelRate: 'Bekor qilinganlar', last12: 'so‘nggi 12 kun', byBrand: 'Brendlar bo‘yicha tushum', pipeline: 'Ishdagi buyurtmalar', attention: 'e’tibor talab qiladi', byHour: 'Soatlar bo‘yicha buyurtmalar', busiest: 'Eng band vaqt', payments: 'To‘lov usullari', districts: 'Tumanlar', topProducts: 'Top mahsulotlar', recent: 'So‘nggi buyurtmalar', seeAll: 'Hammasi', table: 'Jadval', chart: 'Grafik', noPrev: 'taqqoslash uchun ma’lumot yo‘q', hour: 'Soat', share: 'ulush', none: 'Ma’lumot yo‘q' },
  ru: { today: 'Сегодня', d7: '7 дней', d14: '14 дней', revenue: 'Выручка', vsYesterday: 'к вчера', vsPrev: 'к прошлому периоду', orders: 'Заказы', avg: 'Средний чек', items: 'Продано товаров', cancelRate: 'Отмены', last12: 'последние 12 дней', byBrand: 'Выручка по брендам', pipeline: 'Заказы в работе', attention: 'требуют внимания', byHour: 'Заказы по часам', busiest: 'Пиковый час', payments: 'Способы оплаты', districts: 'Районы', topProducts: 'Топ товаров', recent: 'Последние заказы', seeAll: 'Все', table: 'Таблица', chart: 'График', noPrev: 'нет данных для сравнения', hour: 'Час', share: 'доля', none: 'Нет данных' },
  en: { today: 'Today', d7: '7 days', d14: '14 days', revenue: 'Revenue', vsYesterday: 'vs yesterday', vsPrev: 'vs previous period', orders: 'Orders', avg: 'Average order', items: 'Items sold', cancelRate: 'Cancelled', last12: 'last 12 days', byBrand: 'Revenue by brand', pipeline: 'Orders in progress', attention: 'need attention', byHour: 'Orders by hour', busiest: 'Busiest hour', payments: 'Payment methods', districts: 'Districts', topProducts: 'Top products', recent: 'Latest orders', seeAll: 'See all', table: 'Table', chart: 'Chart', noPrev: 'no earlier data to compare', hour: 'Hour', share: 'share', none: 'No data' }
};

const valid = (o: Order) => o.status !== 'cancelled';
const sum = (os: Order[]) => os.reduce((a, o) => a + o.total, 0);
const startOfDay = (offsetDays: number) => { const d = new Date(); d.setHours(0, 0, 0, 0); d.setDate(d.getDate() - offsetDays); return d.getTime(); };
const pct = (cur: number, prev: number) => (prev > 0 ? ((cur - prev) / prev) * 100 : null);

export function Dashboard({ lang, onOpenOrders }: { lang: Language; onOpenOrders: () => void }) {
  const t = ADMIN_TEXT[lang];
  const d = D[lang];
  const orders = useOrders();
  const products = useProducts(true);
  const [period, setPeriod] = useState<Period>('7d');

  const data = useMemo(() => {
    if (!orders) return null;
    const days = period === 'today' ? 1 : period === '7d' ? 7 : 14;
    const from = startOfDay(days - 1);
    const prevFrom = startOfDay(2 * days - 1);
    const at = (o: Order) => new Date(o.createdAt).getTime();
    const inCur = orders.filter((o) => at(o) >= from);
    const inPrev = orders.filter((o) => at(o) >= prevFrom && at(o) < from);
    const cur = inCur.filter(valid), prev = inPrev.filter(valid);

    // trend series: hourly for "today", daily otherwise
    const trend: { label: string; value: number; count: number }[] = [];
    if (period === 'today') {
      const nowH = new Date().getHours();
      for (let h = 8; h <= Math.max(nowH, 20); h++) trend.push({ label: `${h}:00`, value: 0, count: 0 });
      cur.forEach((o) => { const h = new Date(o.createdAt).getHours(); const p = trend.find((x) => x.label === `${h}:00`); if (p) { p.value += o.total; p.count++; } });
    } else {
      for (let i = days - 1; i >= 0; i--) {
        const dd = new Date(startOfDay(i));
        trend.push({ label: `${dd.getDate()}.${String(dd.getMonth() + 1).padStart(2, '0')}`, value: 0, count: 0 });
      }
      cur.forEach((o) => { const idx = Math.floor((at(o) - from) / 86400000); if (trend[idx]) { trend[idx].value += o.total; trend[idx].count++; } });
    }

    // 12-day daily series for the stat-tile sparklines
    const spark = Array.from({ length: 12 }, (_, i) => {
      const s = startOfDay(11 - i), e = s + 86400000;
      const dayOrders = orders.filter((o) => at(o) >= s && at(o) < e);
      const v = dayOrders.filter(valid);
      return { orders: v.length, avg: v.length ? sum(v) / v.length : 0, items: v.reduce((a, o) => a + o.items.reduce((b, i) => b + i.quantity, 0), 0), cancel: dayOrders.length ? (dayOrders.length - v.length) / dayOrders.length * 100 : 0 };
    });

    const items = (os: Order[]) => os.reduce((a, o) => a + o.items.reduce((b, i) => b + i.quantity, 0), 0);
    const cancelRate = (all: Order[]) => (all.length ? ((all.length - all.filter(valid).length) / all.length) * 100 : 0);

    // brand split (by line items so mixed orders split fairly)
    const brandRev: Record<string, number> = { secret_flowers: 0, green_mood: 0, secret_berries: 0 };
    cur.forEach((o) => o.items.forEach((i) => { brandRev[i.brand] = (brandRev[i.brand] ?? 0) + i.price * i.quantity; }));

    // pipeline counts are "right now", not period-bound
    const pipe: OrderStatus[] = ['new', 'confirmed', 'assembling', 'in_transit'];
    const pipeline = pipe.map((s) => ({ status: s, count: orders.filter((o) => o.status === s).length }));

    const hours = Array.from({ length: 24 }, (_, h) => ({ h, count: 0 }));
    cur.forEach((o) => hours[new Date(o.createdAt).getHours()].count++);

    const tally = <K extends string>(key: (o: Order) => K) => {
      const m = new Map<K, { count: number; revenue: number }>();
      cur.forEach((o) => { const k = key(o); const v = m.get(k) ?? { count: 0, revenue: 0 }; v.count++; v.revenue += o.total; m.set(k, v); });
      return [...m.entries()].map(([k, v]) => ({ key: k, ...v })).sort((a, b) => b.count - a.count);
    };

    const sold = new Map<string, { id: string; qty: number; revenue: number }>();
    cur.forEach((o) => o.items.forEach((i) => { const s = sold.get(i.productId) ?? { id: i.productId, qty: 0, revenue: 0 }; s.qty += i.quantity; s.revenue += i.price * i.quantity; sold.set(i.productId, s); }));

    return {
      revenue: sum(cur), revenueDelta: pct(sum(cur), sum(prev)),
      orders: cur.length, ordersDelta: pct(cur.length, prev.length),
      avg: cur.length ? sum(cur) / cur.length : 0, avgDelta: pct(cur.length ? sum(cur) / cur.length : 0, prev.length ? sum(prev) / prev.length : 0),
      items: items(cur), itemsDelta: pct(items(cur), items(prev)),
      cancel: cancelRate(inCur), cancelDelta: inPrev.length ? cancelRate(inCur) - cancelRate(inPrev) : null,
      trend, spark, brandRev, pipeline, hours,
      payments: tally((o) => o.payment.method as PaymentMethod),
      districts: tally((o) => o.delivery.district).slice(0, 5),
      top: [...sold.values()].sort((a, b) => b.revenue - a.revenue).slice(0, 5),
      recent: orders.slice(0, 6)
    };
  }, [orders, period]);

  if (!data) return <div className="text-neutral-500 text-sm">…</div>;
  const productById = new Map((products ?? []).map((p) => [p.id, p]));
  const cmp = period === 'today' ? d.vsYesterday : d.vsPrev;

  return (
    <div className="space-y-5">
      {/* Header + period switch */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="font-serif text-3xl text-white">{t.dashboard}</h1>
        <div className="inline-flex p-1 rounded-xl bg-white/5 border border-white/10" role="tablist" aria-label="Period">
          {(['today', '7d', '14d'] as Period[]).map((p) => (
            <button key={p} role="tab" aria-selected={period === p} onClick={() => setPeriod(p)}
              className={`min-h-[36px] px-4 rounded-lg text-xs font-semibold cursor-pointer ${period === p ? 'bg-[#d7a9a3] text-[#291823]' : 'text-neutral-400 hover:text-white'}`}>
              {p === 'today' ? d.today : p === '7d' ? d.d7 : d.d14}
            </button>
          ))}
        </div>
      </div>

      {/* 1. Hero: revenue + trend line */}
      <Card className="p-5 sm:p-6">
        <div className="grid lg:grid-cols-[260px_1fr] gap-6 items-center">
          <div>
            <div className="text-xs text-neutral-400">{d.revenue} · {period === 'today' ? d.today : period === '7d' ? d.d7 : d.d14}</div>
            <div className="mt-2 text-[40px] sm:text-5xl font-semibold text-white leading-none break-words">{formatShort(data.revenue)}</div>
            <div className="text-sm text-neutral-400 mt-1">{formatSum(data.revenue)}</div>
            <Delta value={data.revenueDelta} label={cmp} noPrev={d.noPrev} className="mt-3" />
          </div>
          <LineChart points={data.trend} lang={lang} />
        </div>
      </Card>

      {/* 2. KPI tiles with sparklines */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
        <StatTile label={d.orders} value={String(data.orders)} delta={data.ordersDelta} cmp={cmp} noPrev={d.noPrev} series={data.spark.map((s) => s.orders)} foot={d.last12} />
        <StatTile label={d.avg} value={formatShort(data.avg)} delta={data.avgDelta} cmp={cmp} noPrev={d.noPrev} series={data.spark.map((s) => s.avg)} foot={d.last12} />
        <StatTile label={d.items} value={String(data.items)} delta={data.itemsDelta} cmp={cmp} noPrev={d.noPrev} series={data.spark.map((s) => s.items)} foot={d.last12} />
        <StatTile label={d.cancelRate} value={`${data.cancel.toFixed(0)}%`} delta={data.cancelDelta} deltaIsPoints upIsGood={false} cmp={cmp} noPrev={d.noPrev} series={data.spark.map((s) => s.cancel)} foot={d.last12} />
      </div>

      {/* 3. Brand split + pipeline */}
      <div className="grid lg:grid-cols-2 gap-5">
        <Card className="p-5">
          <h2 className="text-sm font-semibold text-neutral-200 mb-4">{d.byBrand}</h2>
          <BrandSplit rev={data.brandRev} lang={lang} none={d.none} />
        </Card>
        <Card className="p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-neutral-200">{d.pipeline}</h2>
            <button onClick={onOpenOrders} className="inline-flex items-center gap-1 text-xs text-[#d7a9a3] min-h-[32px] px-2 rounded-lg hover:bg-white/5 cursor-pointer">{d.seeAll}<ArrowRight className="w-3.5 h-3.5" /></button>
          </div>
          <Pipeline steps={data.pipeline} lang={lang} attention={d.attention} onOpen={onOpenOrders} />
        </Card>
      </div>

      {/* 4. Hours / payments / districts */}
      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-5">
        <Card className="p-5 md:col-span-2 xl:col-span-1">
          <h2 className="text-sm font-semibold text-neutral-200 mb-1">{d.byHour}</h2>
          <HourChart hours={data.hours} busiestLabel={d.busiest} none={d.none} />
        </Card>
        <Card className="p-5">
          <h2 className="text-sm font-semibold text-neutral-200 mb-4">{d.payments}</h2>
          <BarList rows={data.payments.map((p) => ({ label: METHOD_LABEL[p.key as PaymentMethod] ?? p.key, value: p.count, sub: formatShort(p.revenue) }))} none={d.none} />
        </Card>
        <Card className="p-5">
          <h2 className="text-sm font-semibold text-neutral-200 mb-4">{d.districts}</h2>
          <BarList rows={data.districts.map((p) => ({ label: p.key.replace(' tumani', ''), value: p.count, sub: formatShort(p.revenue) }))} none={d.none} />
        </Card>
      </div>

      {/* 5. Top products + latest orders */}
      <div className="grid lg:grid-cols-2 gap-5">
        <Card className="p-5">
          <h2 className="text-sm font-semibold text-neutral-200 mb-4">{d.topProducts}</h2>
          {data.top.length === 0 ? <p className="text-sm text-neutral-500">{d.none}</p> : (
            <ol className="space-y-3">
              {data.top.map((b, i) => {
                const p = productById.get(b.id);
                const w = (b.revenue / data.top[0].revenue) * 100;
                return (
                  <li key={b.id} className="flex items-center gap-3">
                    <span className="w-4 text-xs text-neutral-500 tabular-nums">{i + 1}</span>
                    <SafeImage src={p ? thumbOf(p.images[0]) : ''} alt="" className="w-10 h-10 rounded-lg object-cover shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between gap-2 text-sm"><span className="text-neutral-100 truncate">{p?.title[lang] ?? b.id}</span><span className="text-neutral-200 whitespace-nowrap">{formatShort(b.revenue)}</span></div>
                      <div className="mt-1.5 flex items-center gap-2">
                        <div className="flex-1 h-1.5 rounded-full bg-white/5"><div className="h-1.5 rounded-full" style={{ width: `${w}%`, background: p ? BRAND_COLOR[p.brand] : ACCENT }} /></div>
                        <span className="text-[11px] text-neutral-400 tabular-nums w-14 text-right">{b.qty} {t.sold}</span>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ol>
          )}
        </Card>
        <Card className="p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-neutral-200">{d.recent}</h2>
            <button onClick={onOpenOrders} className="inline-flex items-center gap-1 text-xs text-[#d7a9a3] min-h-[32px] px-2 rounded-lg hover:bg-white/5 cursor-pointer">{d.seeAll}<ArrowRight className="w-3.5 h-3.5" /></button>
          </div>
          <ul className="divide-y divide-white/5">
            {data.recent.map((o) => (
              <li key={o.id}>
                <button onClick={onOpenOrders} className="w-full flex items-center gap-3 py-2.5 text-left cursor-pointer hover:bg-white/[0.03] rounded-lg px-1">
                  <SafeImage src={thumbOf(o.items[0]?.productImage ?? '')} alt="" className="w-9 h-9 rounded-lg object-cover shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-neutral-100 truncate">#{o.orderNumber} · {o.customer.name}</div>
                    <div className="text-[11px] text-neutral-500">{formatDateTime(o.createdAt, lang)}</div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-sm text-white">{formatShort(o.total)}</div>
                    <StatusBadge status={o.status} lang={lang} />
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}

/* ----------------------------------------------------------------- widgets */

/** Width of an element in CSS pixels, so SVG charts draw at real size (text stays readable on phones). */
function useWidth<T extends HTMLElement>(fallback: number) {
  const ref = useRef<T>(null);
  const [w, setW] = useState(fallback);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const update = () => setW(Math.max(240, Math.round(el.getBoundingClientRect().width)));
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, w] as const;
}

function Delta({ value, label, noPrev, upIsGood = true, points, className = '', stacked }: { value: number | null; label: string; noPrev: string; upIsGood?: boolean; points?: boolean; className?: string; stacked?: boolean }) {
  if (value === null || !isFinite(value)) return <div className={`text-xs text-neutral-500 ${stacked ? 'text-[10px] leading-tight' : ''} ${className}`}>{noPrev}</div>;
  const flat = Math.abs(value) < 0.5;
  const good = flat ? null : (value > 0) === upIsGood;
  const Icon = flat ? Minus : value > 0 ? ArrowUpRight : ArrowDownRight;
  const color = good === null ? 'text-neutral-400' : good ? 'text-emerald-300' : 'text-red-300';
  return (
    <div className={`${stacked ? 'flex flex-col' : 'inline-flex items-center gap-1'} text-xs ${className}`}>
      <span className={`inline-flex items-center gap-0.5 font-semibold ${color}`}><Icon className="w-3.5 h-3.5" aria-hidden="true" />{value > 0 ? '+' : ''}{value.toFixed(0)}{points ? ' pp' : '%'}</span>
      <span className={`text-neutral-500 ${stacked ? 'text-[10px] leading-tight mt-0.5' : ''}`}>{label}</span>
    </div>
  );
}

function StatTile({ label, value, delta, cmp, noPrev, series, foot, upIsGood = true, deltaIsPoints }: { label: string; value: string; delta: number | null; cmp: string; noPrev: string; series: number[]; foot: string; upIsGood?: boolean; deltaIsPoints?: boolean }) {
  return (
    <Card className="p-4 flex flex-col">
      <div className="text-xs text-neutral-400">{label}</div>
      <div className="mt-1 text-2xl sm:text-3xl font-semibold text-white">{value}</div>
      <Delta value={delta} label={cmp} noPrev={noPrev} upIsGood={upIsGood} points={deltaIsPoints} className="mt-1" stacked />
      <Sparkline values={series} />
      <div className="text-[10px] text-neutral-500 mt-1">{foot}</div>
    </Card>
  );
}

/** 12-point sparkline: history in the de-emphasis hue, today's point in the accent. */
function Sparkline({ values }: { values: number[] }) {
  const W = 120, H = 32, max = Math.max(1, ...values);
  const pts = values.map((v, i) => [ (i / (values.length - 1)) * (W - 4) + 2, H - 3 - (v / max) * (H - 6) ]);
  const last = pts[pts.length - 1];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-8 mt-3" aria-hidden="true" preserveAspectRatio="none">
      <polyline points={pts.map((p) => p.join(',')).join(' ')} fill="none" stroke={MUTED} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
      <circle cx={last[0]} cy={last[1]} r="3" fill={ACCENT} />
    </svg>
  );
}

/** Single-series line with soft area, crosshair + tooltip that snaps to the nearest point. */
function LineChart({ points, lang }: { points: { label: string; value: number; count: number }[]; lang: Language }) {
  const t = ADMIN_TEXT[lang];
  const [hover, setHover] = useState<number | null>(null);
  const [asTable, setAsTable] = useState(false);
  const ref = useRef<SVGSVGElement>(null);
  const [box, W] = useWidth<HTMLDivElement>(640);
  const H = W < 480 ? 170 : 200, padL = 40, padR = 10, padT = 10, padB = 24;
  const max = Math.max(1, ...points.map((p) => p.value));
  const step = Math.pow(10, Math.floor(Math.log10(max)));
  const top = Math.ceil(max / step) * step;
  const x = (i: number) => padL + (points.length === 1 ? (W - padL - padR) / 2 : (i / (points.length - 1)) * (W - padL - padR));
  const y = (v: number) => padT + (H - padT - padB) * (1 - v / top);
  const line = points.map((p, i) => `${i ? 'L' : 'M'}${x(i)},${y(p.value)}`).join(' ');
  const area = `${line} L${x(points.length - 1)},${y(0)} L${x(0)},${y(0)} Z`;
  const every = Math.ceil(points.length / Math.max(3, Math.floor(W / 70)));

  const onMove = (e: RPointerEvent<SVGSVGElement>) => {
    const r = ref.current?.getBoundingClientRect(); if (!r) return;
    const px = ((e.clientX - r.left) / r.width) * W;
    let best = 0, bd = Infinity; points.forEach((_, i) => { const dd = Math.abs(x(i) - px); if (dd < bd) { bd = dd; best = i; } });
    setHover(best);
  };

  return (
    <div ref={box}>
      <div className="flex justify-end -mt-1 mb-1">
        <button onClick={() => setAsTable((v) => !v)} className="text-xs text-neutral-400 hover:text-white min-h-[32px] px-2 cursor-pointer">{asTable ? t.showChart : t.showTable}</button>
      </div>
      {asTable ? (
        <div className="max-h-56 overflow-y-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-neutral-400"><th className="py-1.5 font-medium">{t.day}</th><th className="py-1.5 font-medium text-right">{t.ordersCount}</th><th className="py-1.5 font-medium text-right">{t.sum}</th></tr></thead>
            <tbody>{points.map((p) => <tr key={p.label} className="border-t border-white/5"><td className="py-1.5 text-neutral-300">{p.label}</td><td className="py-1.5 text-right tabular-nums">{p.count}</td><td className="py-1.5 text-right tabular-nums text-white">{formatSum(p.value)}</td></tr>)}</tbody>
          </table>
        </div>
      ) : (
        <div className="relative">
          <svg ref={ref} viewBox={`0 0 ${W} ${H}`} width={W} height={H} className="block max-w-full touch-pan-y" role="img" aria-label={t.revenueByDay}
            onPointerMove={onMove} onPointerDown={onMove} onPointerLeave={() => setHover(null)}>
            <defs><linearGradient id="rev-area" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={ACCENT} stopOpacity="0.28" /><stop offset="100%" stopColor={ACCENT} stopOpacity="0" /></linearGradient></defs>
            {[0, top / 2, top].map((v) => (
              <g key={v}><line x1={padL} x2={W - padR} y1={y(v)} y2={y(v)} stroke="rgba(255,255,255,0.07)" /><text x={padL - 6} y={y(v) + 4} textAnchor="end" fontSize="11" fill="#8a7f86">{formatShort(v)}</text></g>
            ))}
            <path d={area} fill="url(#rev-area)" />
            <path d={line} fill="none" stroke={ACCENT} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
            {points.map((p, i) => (i % every === 0 || i === points.length - 1) && (
              <text key={p.label} x={x(i)} y={H - 6} textAnchor={i === points.length - 1 ? 'end' : i === 0 ? 'start' : 'middle'} fontSize="11" fill="#8a7f86">{p.label}</text>
            ))}
            {hover !== null && (
              <g>
                <line x1={x(hover)} x2={x(hover)} y1={padT} y2={y(0)} stroke="rgba(255,255,255,0.35)" strokeWidth="1" />
                <circle cx={x(hover)} cy={y(points[hover].value)} r="5" fill={ACCENT} stroke="#171016" strokeWidth="2" />
              </g>
            )}
          </svg>
          {hover !== null && (
            <div className="pointer-events-none absolute top-0 z-10 rounded-xl bg-[#241820] border border-white/15 px-3 py-2 text-xs shadow-xl"
              style={{ left: `clamp(0px, calc(${(x(hover) / W) * 100}% - 70px), calc(100% - 150px))` }}>
              <div className="text-neutral-400">{points[hover].label}</div>
              <div className="text-white font-semibold">{formatSum(points[hover].value)}</div>
              <div className="text-neutral-400">{t.ordersCount}: {points[hover].count}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/** Part-to-whole as one 100% stacked bar (2px gaps), with a labelled legend row per brand. */
function BrandSplit({ rev, lang, none }: { rev: Record<string, number>; lang: Language; none: string }) {
  const total = BRANDS.reduce((a, b) => a + (rev[b] ?? 0), 0);
  const [hover, setHover] = useState<string | null>(null);
  if (!total) return <p className="text-sm text-neutral-500">{none}</p>;
  return (
    <div>
      <div className="flex h-4 gap-[2px] rounded-full overflow-hidden" role="img" aria-label={BRANDS.map((b) => `${BRAND_LABEL[b]} ${Math.round(((rev[b] ?? 0) / total) * 100)}%`).join(', ')}>
        {BRANDS.filter((b) => rev[b] > 0).map((b) => (
          <div key={b} onPointerEnter={() => setHover(b)} onPointerLeave={() => setHover(null)} title={`${BRAND_LABEL[b]}: ${formatSum(rev[b])}`}
            style={{ width: `${(rev[b] / total) * 100}%`, background: BRAND_COLOR[b], opacity: hover && hover !== b ? 0.45 : 1 }} className="h-full transition-opacity" />
        ))}
      </div>
      <ul className="mt-5 space-y-3">
        {BRANDS.map((b) => (
          <li key={b} className={`flex items-center gap-3 text-sm transition-opacity ${hover && hover !== b ? 'opacity-50' : ''}`} onPointerEnter={() => setHover(b)} onPointerLeave={() => setHover(null)}>
            <span className="w-3 h-3 rounded-sm shrink-0" style={{ background: BRAND_COLOR[b] }} aria-hidden="true" />
            <span className="flex-1 text-neutral-200">{BRAND_LABEL[b]}</span>
            <span className="text-neutral-400 tabular-nums w-12 text-right">{Math.round(((rev[b] ?? 0) / total) * 100)}%</span>
            <span className="text-white tabular-nums w-20 text-right">{formatShort(rev[b] ?? 0)}</span>
          </li>
        ))}
      </ul>
      <span className="sr-only">{lang}</span>
    </div>
  );
}

const PIPE_ICON = { new: CircleDot, confirmed: BadgeCheck, assembling: Package, in_transit: Truck } as const;

/** Live workflow: how many orders sit at each step right now. */
function Pipeline({ steps, lang, attention, onOpen }: { steps: { status: OrderStatus; count: number }[]; lang: Language; attention: string; onOpen: () => void }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
      {steps.map((s, i) => {
        const Icon = PIPE_ICON[s.status as keyof typeof PIPE_ICON] ?? CircleDot;
        const hot = s.status === 'new' && s.count > 0;
        return (
          <button key={s.status} onClick={onOpen}
            className={`relative text-left rounded-xl p-3 border cursor-pointer transition-colors ${hot ? 'border-amber-400/50 bg-amber-400/10' : 'border-white/10 bg-white/[0.03] hover:bg-white/[0.06]'}`}>
            <Icon className={`w-4 h-4 ${hot ? 'text-amber-300' : 'text-neutral-400'}`} aria-hidden="true" />
            <div className="mt-2 text-2xl font-semibold text-white">{s.count}</div>
            <div className="text-[11px] text-neutral-400 leading-tight">{STATUS_LABEL[lang][s.status]}</div>
            {hot && <div className="text-[10px] text-amber-300 mt-1">{attention}</div>}
            {i < steps.length - 1 && <ArrowRight className="hidden sm:block absolute -right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-neutral-600 z-10" aria-hidden="true" />}
          </button>
        );
      })}
    </div>
  );
}

/** Column chart of orders per hour (8:00–22:00), busiest hour called out. */
function HourChart({ hours, busiestLabel, none }: { hours: { h: number; count: number }[]; busiestLabel: string; none: string }) {
  const [hover, setHover] = useState<number | null>(null);
  const range = hours.filter((x) => x.h >= 8 && x.h <= 22);
  const max = Math.max(0, ...range.map((x) => x.count));
  if (!max) return <p className="text-sm text-neutral-500 mt-3">{none}</p>;
  const busiest = range.reduce((a, b) => (b.count > a.count ? b : a));
  return <HourBars range={range} max={max} busiest={busiest} busiestLabel={busiestLabel} hover={hover} setHover={setHover} />;
}

function HourBars({ range, max, busiest, busiestLabel, hover, setHover }: { range: { h: number; count: number }[]; max: number; busiest: { h: number }; busiestLabel: string; hover: number | null; setHover: (i: number | null) => void }) {
  const [box, W] = useWidth<HTMLDivElement>(360);
  const H = 130, padB = 18, slot = W / range.length, bw = Math.max(6, Math.min(22, slot - 6));
  return (
    <div ref={box}>
      <div className="text-xs text-neutral-400 mb-2">{busiestLabel}: <b className="text-white">{busiest.h}:00–{busiest.h + 1}:00</b></div>
      <div className="relative">
        <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} className="block max-w-full" onPointerLeave={() => setHover(null)} role="img" aria-label={busiestLabel}>
          {range.map((x, i) => {
            const bh = (x.count / max) * (H - padB - 8);
            const bx = i * slot + (slot - bw) / 2, by = H - padB - bh;
            const r = Math.min(4, bh / 2, bw / 2);
            return (
              <g key={x.h} onPointerEnter={() => setHover(i)} onPointerDown={() => setHover(i)}>
                <rect x={i * slot} y={0} width={slot} height={H - padB} fill="transparent" />
                {bh > 0 && <path d={`M${bx},${by + bh} V${by + r} Q${bx},${by} ${bx + r},${by} H${bx + bw - r} Q${bx + bw},${by} ${bx + bw},${by + r} V${by + bh} Z`} fill={x.h === busiest.h ? ACCENT : MUTED} opacity={hover === null || hover === i ? 1 : 0.5} />}
                {x.h % 2 === 0 && <text x={i * slot + slot / 2} y={H - 4} textAnchor="middle" fontSize="10" fill="#8a7f86">{x.h}</text>}
              </g>
            );
          })}
          <line x1="0" x2={W} y1={H - padB} y2={H - padB} stroke="rgba(255,255,255,0.18)" />
        </svg>
        {hover !== null && (
          <div className="pointer-events-none absolute -top-2 rounded-lg bg-[#241820] border border-white/15 px-2 py-1 text-xs text-white shadow-xl"
            style={{ left: `clamp(0px, calc(${((hover + 0.5) / range.length) * 100}% - 40px), calc(100% - 80px))` }}>
            {range[hover].h}:00 · <b>{range[hover].count}</b>
          </div>
        )}
      </div>
    </div>
  );
}

/** Ranked list with inline bars (single hue), value and a secondary figure. */
function BarList({ rows, none }: { rows: { label: string; value: number; sub: string }[]; none: string }) {
  if (!rows.length) return <p className="text-sm text-neutral-500">{none}</p>;
  const max = Math.max(...rows.map((r) => r.value));
  return (
    <ul className="space-y-3">
      {rows.map((r) => (
        <li key={r.label}>
          <div className="flex justify-between gap-2 text-sm"><span className="text-neutral-200 truncate">{r.label}</span><span className="text-neutral-400 whitespace-nowrap"><b className="text-white font-semibold">{r.value}</b> · {r.sub}</span></div>
          <div className="mt-1.5 h-1.5 rounded-full bg-white/5"><div className="h-1.5 rounded-full" style={{ width: `${(r.value / max) * 100}%`, background: ACCENT }} /></div>
        </li>
      ))}
    </ul>
  );
}

// keep dayKey import used (shared helper for callers)
void dayKey;
