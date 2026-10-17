import { useEffect, useState } from 'react';
import { Order, Product } from '../types';
import { getOrders, getProducts, onStoreChange } from './store';

/** Live list of products (re-reads automatically when the admin saves). null while loading. */
export function useProducts(includeHidden = false): Product[] | null {
  const [list, setList] = useState<Product[] | null>(null);
  useEffect(() => {
    let alive = true;
    const load = () =>
      getProducts({ includeHidden })
        .then((p) => alive && setList(p))
        .catch((e) => console.error('[Secret] could not load products', e));
    load();
    const off = onStoreChange(load);
    return () => {
      alive = false;
      off();
    };
  }, [includeHidden]);
  return list;
}

/** Live list of orders, newest first. null while loading. */
export function useOrders(): Order[] | null {
  const [list, setList] = useState<Order[] | null>(null);
  useEffect(() => {
    let alive = true;
    const load = () =>
      getOrders()
        .then((o) => alive && setList(o))
        .catch((e) => console.error('[Secret] could not load orders', e));
    load();
    const off = onStoreChange(load);
    return () => {
      alive = false;
      off();
    };
  }, []);
  return list;
}
