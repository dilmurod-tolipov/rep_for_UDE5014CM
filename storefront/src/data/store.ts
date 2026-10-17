/**
 * DATA LAYER — the one place the site reads and saves products and orders.
 *
 * Today (demo): everything is kept in this browser's localStorage, so the shop and the
 * admin panel on the same computer share data, and nothing reaches a server.
 *
 * Moving to GCP later: keep these function names and signatures, and replace their bodies
 * with fetch() calls to your backend (for example Cloud Run + Firestore or Cloud SQL):
 *   getProducts   -> GET    /api/products?includeHidden=1
 *   saveProduct   -> PUT    /api/products/:id          (admin only)
 *   deleteProduct -> DELETE /api/products/:id          (admin only)
 *   getOrders     -> GET    /api/orders                (admin only)
 *   createOrder   -> POST   /api/orders
 *   updateOrder   -> PATCH  /api/orders/:id            (admin only)
 * The screens only use this file, so nothing else has to change.
 */
import { Order, Product } from '../types';
import { PRODUCTS } from './products';
import { buildDemoOrders } from './demoSeed';

/** Bump when the built-in catalog in products.ts changes, so browsers pick up the new catalog. */
export const CATALOG_VERSION = '2026-09-21a';

const KEY_PRODUCTS = 'secret.products.v1';
const KEY_ORDERS = 'secret.orders.v1';
const KEY_CATALOG_VERSION = 'secret.catalogVersion';
const CHANGE_EVENT = 'secret-store-change';

export class StoreError extends Error {
  constructor(public code: 'storage_full' | 'not_found' | 'unavailable', message: string) {
    super(message);
  }
}

// ---------- low-level storage (safe on phones with storage disabled / private mode) ----------
const memory = new Map<string, string>();

function rawGet(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return memory.get(key) ?? null;
  }
}

function rawSet(key: string, value: string) {
  try {
    window.localStorage.setItem(key, value);
  } catch (err) {
    const name = (err as DOMException)?.name ?? '';
    if (name === 'QuotaExceededError' || name === 'NS_ERROR_DOM_QUOTA_REACHED') {
      throw new StoreError('storage_full', 'Browser storage is full (too many or too large photos).');
    }
    memory.set(key, value); // storage blocked: keep for this session only
  }
}

function readJSON<T>(key: string, fallback: T): T {
  const raw = rawGet(key);
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function writeJSON(key: string, value: unknown) {
  rawSet(key, JSON.stringify(value));
  window.dispatchEvent(new CustomEvent(CHANGE_EVENT));
}

// ---------- seeding ----------
function ensureSeeded() {
  if (rawGet(KEY_CATALOG_VERSION) !== CATALOG_VERSION || !rawGet(KEY_PRODUCTS)) {
    rawSet(KEY_PRODUCTS, JSON.stringify(PRODUCTS));
    rawSet(KEY_CATALOG_VERSION, CATALOG_VERSION);
  }
  if (!rawGet(KEY_ORDERS)) {
    rawSet(KEY_ORDERS, JSON.stringify(buildDemoOrders(PRODUCTS)));
  }
}

const nowISO = () => new Date().toISOString();

// ---------- products ----------
export async function getProducts(opts: { includeHidden?: boolean } = {}): Promise<Product[]> {
  ensureSeeded();
  const list = readJSON<Product[]>(KEY_PRODUCTS, PRODUCTS);
  return opts.includeHidden ? list : list.filter((p) => !p.hidden);
}

export async function saveProduct(product: Product): Promise<Product> {
  ensureSeeded();
  const list = readJSON<Product[]>(KEY_PRODUCTS, PRODUCTS);
  const saved = { ...product, updatedAt: nowISO() };
  const i = list.findIndex((p) => p.id === product.id);
  if (i >= 0) list[i] = saved;
  else list.unshift(saved);
  writeJSON(KEY_PRODUCTS, list);
  return saved;
}

export async function deleteProduct(id: string): Promise<void> {
  ensureSeeded();
  const list = readJSON<Product[]>(KEY_PRODUCTS, PRODUCTS).filter((p) => p.id !== id);
  writeJSON(KEY_PRODUCTS, list);
}

export function newProductId(brand: Product['brand']): string {
  const prefix = brand === 'secret_flowers' ? 'fl' : brand === 'secret_berries' ? 'sb' : 'gm';
  return `${prefix}-${Date.now().toString(36)}`;
}

// ---------- orders ----------
export async function getOrders(): Promise<Order[]> {
  ensureSeeded();
  return readJSON<Order[]>(KEY_ORDERS, []).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}

export async function createOrder(order: Order): Promise<Order> {
  ensureSeeded();
  const list = readJSON<Order[]>(KEY_ORDERS, []);
  const saved = { ...order, updatedAt: nowISO() };
  list.unshift(saved);
  writeJSON(KEY_ORDERS, list);
  return saved;
}

export async function updateOrder(id: string, patch: Partial<Order>): Promise<Order> {
  ensureSeeded();
  const list = readJSON<Order[]>(KEY_ORDERS, []);
  const i = list.findIndex((o) => o.id === id);
  if (i < 0) throw new StoreError('not_found', `Order ${id} not found`);
  list[i] = { ...list[i], ...patch, updatedAt: nowISO() };
  writeJSON(KEY_ORDERS, list);
  return list[i];
}

// ---------- demo helpers ----------
/** Put the catalog and sample orders back to how they came. */
export async function resetDemoData(): Promise<void> {
  rawSet(KEY_PRODUCTS, JSON.stringify(PRODUCTS));
  rawSet(KEY_CATALOG_VERSION, CATALOG_VERSION);
  writeJSON(KEY_ORDERS, buildDemoOrders(PRODUCTS));
}

/** Call cb whenever data changes (in this tab or another tab of the same browser). */
export function onStoreChange(cb: () => void): () => void {
  const onStorage = (e: StorageEvent) => {
    if (!e.key || e.key.startsWith('secret.')) cb();
  };
  window.addEventListener(CHANGE_EVENT, cb);
  window.addEventListener('storage', onStorage);
  return () => {
    window.removeEventListener(CHANGE_EVENT, cb);
    window.removeEventListener('storage', onStorage);
  };
}
