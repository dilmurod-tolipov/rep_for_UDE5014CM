export type Language = 'uz' | 'ru' | 'en';
export type ThemeMode = 'dark' | 'light';

export type BrandCategory = 'all' | 'secret_flowers' | 'green_mood' | 'secret_berries';

export interface Product {
  id: string;
  brand: 'secret_flowers' | 'green_mood' | 'secret_berries';
  title: Record<Language, string>;
  subtitle: Record<Language, string>;
  description: Record<Language, string>;
  price: number; // in UZS
  oldPrice?: number;
  rating: number;
  reviewsCount: number;
  images: string[];
  category: string;
  tags: string[];
  inStock?: boolean;
  /** Hidden products stay in the admin but are not shown in the shop. */
  hidden?: boolean;
  /** Last time the product was edited in the admin (ISO date). */
  updatedAt?: string;
  isBestseller?: boolean;
  isNew?: boolean;
  prepTimeMinutes: number;
  composition: Record<Language, string[]>;
  careTips: Record<Language, string[]>;
  dimensions: string;
}

export interface CartItem {
  cartItemId: string;
  product: Product;
  quantity: number;
  selectedAddOns: {
    id: string;
    name: Record<Language, string>;
    price: number;
  }[];
  cardMessage?: string;
  recipientName?: string;
  customRibbon?: string;
}

export type PaymentMethod = 'payme' | 'click' | 'uzumpay' | 'card' | 'cash';

export type OrderStatus = 'new' | 'confirmed' | 'assembling' | 'quality_check' | 'in_transit' | 'delivered' | 'cancelled';

export interface CourierInfo {
  id: string;
  name: string;
  phone: string;
  vehicle: string;
  status: 'available' | 'delivering' | 'offline';
  rating: number;
  activeOrders: number;
}

export interface Order {
  id: string;
  orderNumber: string;
  createdAt: string;
  brand: 'secret_flowers' | 'green_mood' | 'secret_berries' | 'mixed';
  items: {
    productId: string;
    productTitle: Record<Language, string>;
    productImage: string;
    quantity: number;
    price: number;
    brand: string;
    cardMessage?: string;
  }[];
  customer: {
    name: string;
    phone: string;
    email?: string;
  };
  recipient: {
    isRecipientCustomer: boolean;
    name: string;
    phone: string;
    isSurprise: boolean;
  };
  delivery: {
    district: string;
    address: string;
    apartment?: string;
    landmark?: string;
    date: string;
    timeSlot: string;
    type: 'express' | 'scheduled';
  };
  cardMessage?: string;
  payment: {
    method: PaymentMethod;
    status: 'pending' | 'paid' | 'cash_on_delivery';
    transactionId?: string;
    paidAt?: string;
  };
  status: OrderStatus;
  subtotal: number;
  deliveryFee: number;
  discount: number;
  total: number;
  courier?: {
    id: string;
    name: string;
    phone: string;
    assignedAt?: string;
    etaMinutes?: number;
    vehicle: string;
  };
  qualityCheckPhoto?: string;
  notes?: string;
  /** Admin-only internal note. */
  adminNote?: string;
  /** True for generated sample orders (so the dashboard can say so). */
  isDemo?: boolean;
  updatedAt?: string;
}

export interface CustomBouquetConfig {
  boxType: 'velvet_black' | 'cream_hatbox' | 'kraft_wrap' | 'crystal_vase';
  focalFlower: 'peonies' | 'ecuador_roses' | 'hydrangeas' | 'lisianthus';
  flowerColor: 'crimson' | 'blush' | 'pure_white' | 'pastel_blue' | 'lavender';
  flowerQuantity: number;
  foliage: 'eucalyptus' | 'babys_breath' | 'lavender_sprigs' | 'none';
  ribbonColor: 'champagne' | 'burgundy' | 'emerald' | 'rose_gold';
  waxSealMonogram: 'S' | 'G' | 'Love' | 'None';
  cardText: string;
}
