/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Search,
  Filter,
  Sparkles,
  Truck,
  ShieldCheck,
  Award,
  Clock,
  Instagram,
  ArrowRight,
  Layers,
  CheckCircle2,
  Heart
} from 'lucide-react';
import { Language, ThemeMode, Product, CartItem, Order, OrderStatus, CourierInfo } from './types';
import { TRANSLATIONS } from './translations';
import { PRODUCTS, ADDONS_CATALOG } from './data/products';
import { createOrder, updateOrder } from './data/store';
import { useProducts } from './data/useStore';
import { soundManager } from './utils/audio';

// Components
import { Preloader } from './components/Preloader';
import { PetalsCanvas } from './components/PetalsCanvas';
import { Navbar } from './components/Navbar';
import { ParallaxHero } from './components/ParallaxHero';
import { BrandShowcase } from './components/BrandShowcase';
import { ProductCard } from './components/ProductCard';
import { ProductDetailModal } from './components/ProductDetailModal';
import { BouquetBuilder } from './components/BouquetBuilder';
import { CartDrawer } from './components/CartDrawer';
import { CheckoutModal } from './components/CheckoutModal';
import { PaymentModal } from './components/PaymentModal';
import { Footer } from './components/Footer';
import { CatalogSections, CatalogFilter, SortKey } from './components/CatalogSections';
import { ErrorBoundary } from './components/ErrorBoundary';
import { DemoBar, DEMO_MODE, DEMO_TEXT } from './components/DemoNotice';

export default function App() {
  // App-level state
  const [theme, setTheme] = useState<ThemeMode>('dark');
  const [lang, setLang] = useState<Language>('uz');
  // The opening film plays on every page load (it can be skipped)
  const [loading, setLoading] = useState(true);

  // Catalog State
  const [selectedBrandFilter, setSelectedBrandFilter] = useState<CatalogFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortKey>('featured');

  // Interactive Modals State
  const [detailProduct, setDetailProduct] = useState<Product | null>(null);
  const [cartOpen, setCartOpen] = useState(false);
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [paymentOrder, setPaymentOrder] = useState<Order | null>(null);

  // Cart & Orders State
  const [cart, setCart] = useState<CartItem[]>([]);
  // Products come from the data layer, so admin edits (prices, hidden items, stock) show up here.
  const catalog = useProducts() ?? PRODUCTS.filter((p) => !p.hidden);

  // Toast alert state
  const [toastMessage, setToastMessage] = useState<{ title: string; subtitle: string } | null>(null);

  const t = TRANSLATIONS[lang];

  // Stop the page behind an open pop-up from scrolling (prevents jumpy scrolling on phones)
  const anyOverlayOpen = Boolean(detailProduct) || cartOpen || checkoutOpen || Boolean(paymentOrder);
  useEffect(() => {
    const body = document.body;
    const prev = body.style.overflow;
    if (anyOverlayOpen) body.style.overflow = 'hidden';
    return () => {
      body.style.overflow = prev;
    };
  }, [anyOverlayOpen]);

  // Tell the browser which language the page is in (correct hyphenation, fonts, screen readers)
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  // Synchronize Dark Theme class on <html>
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  // Trigger Toast Notification
  const showNotification = (title: string, subtitle: string) => {
    setToastMessage({ title, subtitle });
    soundManager.playChime(750);
    setTimeout(() => {
      setToastMessage(null);
    }, 4500);
  };

  // Cart Operations
  const handleAddToCart = (
    product: Product,
    quantity: number = 1,
    cardMessage: string = '',
    selectedAddOns: typeof ADDONS_CATALOG = []
  ) => {
    soundManager.playPluck();

    setCart((prev) => {
      const existingIndex = prev.findIndex(
        (item) =>
          item.product.id === product.id &&
          item.cardMessage === cardMessage &&
          item.selectedAddOns.length === selectedAddOns.length
      );

      if (existingIndex > -1) {
        const updated = [...prev];
        updated[existingIndex].quantity += quantity;
        return updated;
      } else {
        const newItem: CartItem = {
          cartItemId: `ci-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
          product,
          quantity,
          cardMessage,
          selectedAddOns
        };
        return [...prev, newItem];
      }
    });

    showNotification(
      t.addedToCartAlert,
      `${product.title[lang]} (${quantity}x)`
    );
  };

  const handleUpdateCartQty = (cartItemId: string, newQty: number) => {
    if (newQty <= 0) {
      handleRemoveCartItem(cartItemId);
      return;
    }
    setCart((prev) =>
      prev.map((item) => (item.cartItemId === cartItemId ? { ...item, quantity: newQty } : item))
    );
  };

  const handleRemoveCartItem = (cartItemId: string) => {
    setCart((prev) => prev.filter((item) => item.cartItemId !== cartItemId));
  };

  // Add Custom Atelier Bouquet to Cart
  const handleAddCustomBouquet = (customProduct: Product, cardMessage: string) => {
    handleAddToCart(customProduct, 1, cardMessage, []);
    setCartOpen(true);
  };

  // Order Placement & CRM Dispatch
  const handleOrderPlaced = (newOrder: Order) => {
    setCheckoutOpen(false);

    // Work out which brand the order belongs to (for the admin's filters)
    const brands = new Set(newOrder.items.map((i) => i.brand));
    const orderToSave: Order = {
      ...newOrder,
      brand: brands.size === 1 ? (newOrder.items[0].brand as Order['brand']) : 'mixed',
      isDemo: DEMO_MODE
    };

    // Save the order so it appears in the admin panel (status stays "new" until staff confirm it)
    createOrder(orderToSave).catch((e) => console.error('[Secret] could not save order', e));

    // Cash on delivery needs no online payment step
    if (newOrder.payment.method === 'cash') {
      setCart([]);
      showNotification(`${t.toastOrderCreated} · #${newOrder.orderNumber}`, DEMO_MODE ? DEMO_TEXT[lang].done : t.cashDesc);
      return;
    }

    // Open Payment Gateway simulation
    setPaymentOrder(newOrder);

    // Toast alert of order ingestion
    showNotification(
      `${t.toastOrderCreated} · #${newOrder.orderNumber}`,
      DEMO_MODE ? DEMO_TEXT[lang].done : `Syncing with Store CRM & Dispatching Courier...`
    );
  };

  const handlePaymentSuccess = (orderId: string, transactionId: string) => {
    // Record the (simulated) payment on the saved order
    updateOrder(orderId, {
      payment: { ...(paymentOrder?.payment ?? { method: 'payme' }), status: 'paid', transactionId, paidAt: new Date().toISOString() }
    }).catch((e) => console.error('[Secret] could not update order', e));

    // Clear cart
    setCart([]);

    showNotification(
      `${t.toastPaymentReceived} · ${transactionId}`,
      DEMO_MODE ? DEMO_TEXT[lang].done : `Order #${orderId.slice(-4)} sent to Florist Atelier & Courier Bot!`
    );
  };

  // Navigation Smooth Scroll
  const scrollToSection = (sectionId: string) => {
    soundManager.playTick();
    const elem = document.getElementById(sectionId);
    if (elem) {
      elem.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Search and sort; the category split happens inside CatalogSections
  const searchLower = searchQuery.trim().toLowerCase();
  const filteredProducts = catalog
    .filter(
      (product) =>
        !searchLower ||
        product.title[lang].toLowerCase().includes(searchLower) ||
        product.subtitle[lang].toLowerCase().includes(searchLower) ||
        product.tags.some((tag) => tag.toLowerCase().includes(searchLower))
    )
    .sort((a, b) => (sortBy === 'price_asc' ? a.price - b.price : sortBy === 'price_desc' ? b.price - a.price : 0));
  const categoryTotals = {
    secret_flowers: catalog.filter((p) => p.brand === 'secret_flowers').length,
    green_mood: catalog.filter((p) => p.brand === 'green_mood').length,
    secret_berries: catalog.filter((p) => p.brand === 'secret_berries').length
  };

  const totalCartCount = cart.reduce((acc, item) => acc + item.quantity, 0);

  return (
    <div className="min-h-screen bg-white dark:bg-[#0c060b] text-neutral-900 dark:text-[#f7f3f2] selection:bg-[#d7a9a3] selection:text-[#291823] transition-colors duration-400 font-sans relative overflow-x-hidden">
      {/* 3D Preloader */}
      <AnimatePresence>
        {loading && <Preloader lang={lang} onComplete={() => setLoading(false)} />}
      </AnimatePresence>

      {/* Interactive 3D Canvas Background Petals */}
      <ErrorBoundary variant="section">
        <PetalsCanvas theme={theme} />
      </ErrorBoundary>

      {/* Floating System Toast */}
      <AnimatePresence>
        {toastMessage && (
          <motion.div
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            className="fixed top-20 right-4 z-50 p-4 rounded-2xl bg-neutral-900/95 dark:bg-[#1a0f17]/95 text-white dark:text-[#f5ecea] shadow-2xl border border-[#d7a9a3]/40 backdrop-blur-xl flex items-center gap-3 max-w-sm"
          >
            <div className="w-8 h-8 rounded-full bg-[#d7a9a3]/20 text-[#d7a9a3] flex items-center justify-center shrink-0">
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-bold leading-tight line-clamp-1">{toastMessage.title}</p>
              <p className="text-xs opacity-80 mt-0.5 line-clamp-2">{toastMessage.subtitle}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Top Luxury Navigation */}
      <Navbar
        lang={lang}
        cartCount={totalCartCount}
        onOpenCart={() => setCartOpen(true)}
        onSelectLanguage={(l) => setLang(l)}
        onNavigateTo={scrollToSection}
      />

      {/* Main Content Area */}
      <main className="relative z-10 pt-20">
        {/* Parallax 3D Hero Section */}
        <ParallaxHero
          lang={lang}
          theme={theme}
          onExploreCatalog={(brand) => {
            if (brand) setSelectedBrandFilter(brand as CatalogFilter);
            scrollToSection('section-catalog');
          }}
          onOpenAtelier={() => scrollToSection('section-atelier')}
        />

        {/* 3 Brand Profiles Showcase (Secret, Green Mood, Secret Berries) */}
        <BrandShowcase
          lang={lang}
          onSelectBrand={(brandKey) => {
            setSelectedBrandFilter(brandKey as CatalogFilter);
            scrollToSection('section-catalog');
          }}
        />

        {/* Catalog: three categories (Secret Flowers, Green Mood, Secret Berries) */}
        <CatalogSections
          lang={lang}
          heading={t.catalogHeading}
          subheading={t.catalogSubheading}
          products={filteredProducts}
          totals={categoryTotals}
          selected={selectedBrandFilter}
          onSelect={setSelectedBrandFilter}
          searchQuery={searchQuery}
          onSearch={setSearchQuery}
          sortBy={sortBy}
          onSort={setSortBy}
          onQuickView={(p) => setDetailProduct(p)}
          onAddToCart={(p) => handleAddToCart(p, 1, '', [])}
        />

        {/* 3D Atelier: Custom Bouquet & Gift Architect */}
        <ErrorBoundary variant="section">
      <BouquetBuilder
          lang={lang}
          onAddCustomBouquet={handleAddCustomBouquet}
        />
      </ErrorBoundary>

        {/* Value Proposition & Tashkent Logistics Highlight */}
        <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
          <div className="rounded-3xl border border-neutral-200 dark:border-neutral-800 bg-neutral-100/50 dark:bg-neutral-900/40 p-8 sm:p-12 lg:p-16 backdrop-blur-md">
            <div className="text-center max-w-2xl mx-auto mb-12">
              <span className="text-sm uppercase tabular-nums tracking-widest text-amber-600 dark:text-amber-400 font-semibold">
                {t.deliveryKicker}
              </span>
              <h3 className="font-serif text-3xl sm:text-4xl font-light text-neutral-900 dark:text-white mt-2">
                {t.deliveryHeading}
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
              <div className="p-7 sm:p-9 rounded-3xl bg-white dark:bg-neutral-900 border border-neutral-200/60 dark:border-neutral-800/60 shadow-lg">
                <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-3xl bg-rose-500/10 text-rose-500 flex items-center justify-center mx-auto mb-5">
                  <Truck className="w-8 h-8 sm:w-10 sm:h-10" />
                </div>
                <h4 className="font-serif text-2xl sm:text-3xl font-medium text-neutral-900 dark:text-white mb-3">
                  {t.heroFeatureExpress}
                </h4>
                <p className="text-sm sm:text-base text-neutral-500 dark:text-neutral-400 leading-relaxed">
                  {t.deliveryDesc1}
                </p>
              </div>

              <div className="p-7 sm:p-9 rounded-3xl bg-white dark:bg-neutral-900 border border-neutral-200/60 dark:border-neutral-800/60 shadow-lg">
                <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-3xl bg-amber-500/10 text-amber-500 flex items-center justify-center mx-auto mb-5">
                  <Award className="w-8 h-8 sm:w-10 sm:h-10" />
                </div>
                <h4 className="font-serif text-2xl sm:text-3xl font-medium text-neutral-900 dark:text-white mb-3">
                  {t.heroFeatureCard}
                </h4>
                <p className="text-sm sm:text-base text-neutral-500 dark:text-neutral-400 leading-relaxed">
                  {t.deliveryDesc2}
                </p>
              </div>

              <div className="p-7 sm:p-9 rounded-3xl bg-white dark:bg-neutral-900 border border-neutral-200/60 dark:border-neutral-800/60 shadow-lg">
                <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-3xl bg-purple-500/10 text-purple-500 flex items-center justify-center mx-auto mb-5">
                  <ShieldCheck className="w-8 h-8 sm:w-10 sm:h-10" />
                </div>
                <h4 className="font-serif text-2xl sm:text-3xl font-medium text-neutral-900 dark:text-white mb-3">
                  {t.heroFeaturePhoto}
                </h4>
                <p className="text-sm sm:text-base text-neutral-500 dark:text-neutral-400 leading-relaxed">
                  {t.deliveryDesc3}
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <Footer lang={lang} />

      {/* Demo label (remove by setting DEMO_MODE = false in components/DemoNotice.tsx) */}
      <DemoBar lang={lang} />
      {DEMO_MODE && <div className="h-12" aria-hidden="true" />}

      {/* Modals & Slide-overs */}
      <ErrorBoundary variant="section" onReset={() => setDetailProduct(null)}>
      <ProductDetailModal
        key={detailProduct?.id ?? 'none'}
        product={detailProduct}
        isOpen={Boolean(detailProduct)}
        onClose={() => setDetailProduct(null)}
        lang={lang}
        onAddToCart={handleAddToCart}
      />
      </ErrorBoundary>

      <ErrorBoundary variant="section" onReset={() => setCartOpen(false)}>
      <CartDrawer
        isOpen={cartOpen}
        onClose={() => setCartOpen(false)}
        items={cart}
        lang={lang}
        onUpdateQuantity={handleUpdateCartQty}
        onRemoveItem={handleRemoveCartItem}
        onProceedToCheckout={() => {
          setCartOpen(false);
          setCheckoutOpen(true);
        }}
      />
      </ErrorBoundary>

      <ErrorBoundary variant="section" onReset={() => setCheckoutOpen(false)}>
      <CheckoutModal
        isOpen={checkoutOpen}
        onClose={() => setCheckoutOpen(false)}
        cartItems={cart}
        lang={lang}
        onOrderPlaced={handleOrderPlaced}
      />
      </ErrorBoundary>

      <ErrorBoundary variant="section" onReset={() => setPaymentOrder(null)}>
      <PaymentModal
        key={paymentOrder?.id ?? 'none'}
        isOpen={Boolean(paymentOrder)}
        onClose={() => setPaymentOrder(null)}
        order={paymentOrder}
        lang={lang}
        onPaymentSuccess={handlePaymentSuccess}
      />
      </ErrorBoundary>
    </div>
  );
}
