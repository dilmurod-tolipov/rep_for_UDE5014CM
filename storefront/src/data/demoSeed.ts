/**
 * Sample orders so the admin dashboard has something to show in demo mode.
 * Every order here is marked isDemo: true. Names and phone numbers are made up.
 * Dates are generated relative to "now", so "today" always has a few orders.
 */
import { Order, OrderStatus, PaymentMethod, Product } from '../types';

const NAMES = ['Aziza Karimova', 'Dilnoza Rashidova', 'Jasur Toshmatov', 'Madina Yusupova', 'Sardor Aliyev', 'Kamila Rustamova', 'Bekzod Nurmatov', 'Nigora Alimova', 'Shahzod Qodirov', 'Malika Ergasheva', 'Otabek Saidov', 'Zarina Xolmatova'];
const DISTRICTS = ['Mirzo Ulug‘bek tumani', 'Yunusobod tumani', 'Yakkasaroy tumani', 'Mirobod tumani', 'Chilonzor tumani', 'Shayxontohur tumani'];
const METHODS: PaymentMethod[] = ['payme', 'click', 'uzumpay', 'cash', 'payme', 'click'];

function rng(seed: number) {
  let s = seed >>> 0;
  return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;
}

export function buildDemoOrders(products: Product[]): Order[] {
  const rand = rng(20260921);
  const pick = <T,>(arr: T[]) => arr[Math.floor(rand() * arr.length)];
  const now = Date.now();
  const orders: Order[] = [];
  // ~26 orders over the last 14 days, more on recent days
  const perDay = [4, 3, 2, 3, 1, 2, 2, 1, 2, 1, 2, 1, 1, 1];
  let n = 1001;
  perDay.forEach((count, daysAgo) => {
    for (let k = 0; k < count; k++) {
      const hour = 9 + Math.floor(rand() * 11);
      const created = new Date(now - daysAgo * 86400000);
      created.setHours(Math.min(hour, daysAgo === 0 ? Math.max(9, new Date().getHours()) : hour), Math.floor(rand() * 60), 0, 0);
      if (created.getTime() > now) created.setTime(now - (k + 1) * 17 * 60000);

      const lines = 1 + (rand() > 0.7 ? 1 : 0);
      const items = Array.from({ length: lines }, () => {
        const p = pick(products);
        return {
          productId: p.id,
          productTitle: p.title,
          productImage: p.images[0],
          quantity: rand() > 0.85 ? 2 : 1,
          price: p.price,
          brand: p.brand
        };
      });
      const subtotal = items.reduce((a, i) => a + i.price * i.quantity, 0);
      const deliveryFee = subtotal >= 500000 ? 0 : 35000;
      const method = pick(METHODS);

      let status: OrderStatus = 'delivered';
      if (daysAgo === 0) status = pick<OrderStatus>(['new', 'new', 'assembling', 'in_transit', 'confirmed']);
      else if (daysAgo === 1) status = pick<OrderStatus>(['delivered', 'delivered', 'in_transit']);
      if (rand() > 0.93) status = 'cancelled';

      const name = pick(NAMES);
      const brands = new Set(items.map((i) => i.brand));
      orders.push({
        id: `demo-${n}`,
        orderNumber: `SEC-${n}`,
        createdAt: created.toISOString(),
        brand: brands.size > 1 ? 'mixed' : (items[0].brand as Order['brand']),
        items,
        customer: { name, phone: `+998 90 000 ${String(n).slice(-2)} ${String(n).slice(-2)}` },
        recipient: { isRecipientCustomer: rand() > 0.5, name: rand() > 0.5 ? name : pick(NAMES), phone: '+998 90 000 00 00', isSurprise: rand() > 0.6 },
        delivery: {
          district: pick(DISTRICTS),
          address: 'Demo ko‘chasi, ' + (1 + Math.floor(rand() * 90)) + '-uy',
          date: created.toISOString().slice(0, 10),
          timeSlot: rand() > 0.5 ? 'Express (60-90 min)' : '14:00 - 16:00',
          type: rand() > 0.5 ? 'express' : 'scheduled'
        },
        payment: {
          method,
          status: status === 'cancelled' ? 'pending' : method === 'cash' ? (status === 'delivered' ? 'paid' : 'cash_on_delivery') : 'paid'
        },
        status,
        subtotal,
        deliveryFee,
        discount: 0,
        total: subtotal + deliveryFee,
        isDemo: true
      });
      n++;
    }
  });
  return orders;
}
