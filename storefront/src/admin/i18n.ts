import { Language, OrderStatus, PaymentMethod } from '../types';

export const STATUS_FLOW: OrderStatus[] = ['new', 'confirmed', 'assembling', 'in_transit', 'delivered'];

const S = {
  uz: {
    admin: 'Admin panel', signIn: 'Kirish', password: 'Parol', wrongPassword: 'Parol noto‘g‘ri',
    demoLoginHint: 'Demo rejim: parol “secret”. Haqiqiy himoyalangan kirish server (GCP) ulanganda qo‘shiladi.',
    dashboard: 'Bosh sahifa', orders: 'Buyurtmalar', products: 'Mahsulotlar', viewShop: 'Do‘konni ochish', signOut: 'Chiqish',
    resetDemo: 'Demo ma’lumotlarni tiklash', resetConfirm: 'Barcha mahsulot va buyurtmalar dastlabki holatiga qaytadi. Davom etasizmi?',
    demoData: 'Demo ma’lumotlar: faqat shu brauzerda saqlanadi.',
    today: 'Bugun', ordersToday: 'Bugungi buyurtmalar', revenueToday: 'Bugungi tushum', revenue14: '14 kunlik tushum',
    avgOrder: 'O‘rtacha chek', openOrders: 'Faol buyurtmalar', revenueByDay: 'Kunlik tushum (so‘nggi 14 kun)',
    bestSellers: 'Eng ko‘p sotilganlar', byStatus: 'Holat bo‘yicha', showTable: 'Jadval', showChart: 'Grafik',
    day: 'Kun', ordersCount: 'Buyurtmalar', sum: 'Summa', sold: 'dona', noData: 'Hozircha ma’lumot yo‘q',
    all: 'Hammasi', search: 'Qidirish…', searchOrders: 'Raqam, ism yoki telefon', noOrders: 'Buyurtmalar topilmadi',
    customer: 'Buyurtmachi', recipient: 'Qabul qiluvchi', delivery: 'Yetkazish', payment: 'To‘lov', items: 'Mahsulotlar',
    total: 'Jami', subtotal: 'Oraliq summa', deliveryFee: 'Yetkazish', surprise: 'Sovg‘a (kutilmagan)', cardMessage: 'Otkritka matni',
    note: 'Ichki izoh', saveNote: 'Izohni saqlash', saved: 'Saqlandi', nextStep: 'Keyingi bosqich', cancelOrder: 'Bekor qilish',
    reopen: 'Qayta ochish', call: 'Qo‘ng‘iroq', close: 'Yopish', paid: 'To‘langan', pending: 'Kutilmoqda', cod: 'Yetkazilganda',
    demoTag: 'demo',
    addProduct: 'Mahsulot qo‘shish', edit: 'Tahrirlash', delete: 'O‘chirish', deleteConfirm: 'Bu mahsulot o‘chirilsinmi?',
    hidden: 'Yashirin', visible: 'Ko‘rinadi', inStock: 'Sotuvda', soldOut: 'Tugagan', price: 'Narx', save: 'Saqlash', cancel: 'Bekor',
    brand: 'Brend', category: 'Kategoriya', prepTime: 'Tayyorlash (daq.)', photo: 'Rasm', changePhoto: 'Rasmni almashtirish',
    title: 'Nomi', subtitle: 'Qisqa tavsif', description: 'Tavsif', composition: 'Tarkibi (har qatorga bittasi)',
    careTips: 'Parvarish (har qatorga bittasi)', showInShop: 'Do‘konda ko‘rsatish', required: 'To‘ldirish shart',
    storageFull: 'Brauzer xotirasi to‘ldi. Kichikroq rasm tanlang yoki demo ma’lumotlarni tiklang.',
    photoHint: 'JPG/PNG, avtomatik kichraytiriladi', productsCount: 'mahsulot', newProduct: 'Yangi mahsulot'
  },
  ru: {
    admin: 'Админ-панель', signIn: 'Войти', password: 'Пароль', wrongPassword: 'Неверный пароль',
    demoLoginHint: 'Демо-режим: пароль «secret». Настоящий защищённый вход появится с сервером (GCP).',
    dashboard: 'Главная', orders: 'Заказы', products: 'Товары', viewShop: 'Открыть магазин', signOut: 'Выйти',
    resetDemo: 'Сбросить демо-данные', resetConfirm: 'Все товары и заказы вернутся к исходным. Продолжить?',
    demoData: 'Демо-данные: хранятся только в этом браузере.',
    today: 'Сегодня', ordersToday: 'Заказы сегодня', revenueToday: 'Выручка сегодня', revenue14: 'Выручка за 14 дней',
    avgOrder: 'Средний чек', openOrders: 'Активные заказы', revenueByDay: 'Выручка по дням (последние 14 дней)',
    bestSellers: 'Хиты продаж', byStatus: 'По статусам', showTable: 'Таблица', showChart: 'График',
    day: 'День', ordersCount: 'Заказы', sum: 'Сумма', sold: 'шт.', noData: 'Пока нет данных',
    all: 'Все', search: 'Поиск…', searchOrders: 'Номер, имя или телефон', noOrders: 'Заказы не найдены',
    customer: 'Заказчик', recipient: 'Получатель', delivery: 'Доставка', payment: 'Оплата', items: 'Товары',
    total: 'Итого', subtotal: 'Подытог', deliveryFee: 'Доставка', surprise: 'Сюрприз', cardMessage: 'Текст открытки',
    note: 'Внутренняя заметка', saveNote: 'Сохранить заметку', saved: 'Сохранено', nextStep: 'Следующий этап', cancelOrder: 'Отменить',
    reopen: 'Вернуть в работу', call: 'Позвонить', close: 'Закрыть', paid: 'Оплачен', pending: 'Ожидает', cod: 'При получении',
    demoTag: 'демо',
    addProduct: 'Добавить товар', edit: 'Изменить', delete: 'Удалить', deleteConfirm: 'Удалить этот товар?',
    hidden: 'Скрыт', visible: 'Виден', inStock: 'В наличии', soldOut: 'Нет в наличии', price: 'Цена', save: 'Сохранить', cancel: 'Отмена',
    brand: 'Бренд', category: 'Категория', prepTime: 'Сборка (мин.)', photo: 'Фото', changePhoto: 'Заменить фото',
    title: 'Название', subtitle: 'Кратко', description: 'Описание', composition: 'Состав (по строке)',
    careTips: 'Уход (по строке)', showInShop: 'Показывать в магазине', required: 'Обязательно',
    storageFull: 'Память браузера заполнена. Выберите фото поменьше или сбросьте демо-данные.',
    photoHint: 'JPG/PNG, уменьшается автоматически', productsCount: 'товаров', newProduct: 'Новый товар'
  },
  en: {
    admin: 'Admin panel', signIn: 'Sign in', password: 'Password', wrongPassword: 'Wrong password',
    demoLoginHint: 'Demo mode: the password is “secret”. Real secure sign-in comes with the server (GCP).',
    dashboard: 'Dashboard', orders: 'Orders', products: 'Products', viewShop: 'Open shop', signOut: 'Sign out',
    resetDemo: 'Reset demo data', resetConfirm: 'All products and orders go back to the starting data. Continue?',
    demoData: 'Demo data: stored in this browser only.',
    today: 'Today', ordersToday: 'Orders today', revenueToday: 'Revenue today', revenue14: 'Revenue, 14 days',
    avgOrder: 'Average order', openOrders: 'Open orders', revenueByDay: 'Revenue by day (last 14 days)',
    bestSellers: 'Best sellers', byStatus: 'By status', showTable: 'Table', showChart: 'Chart',
    day: 'Day', ordersCount: 'Orders', sum: 'Amount', sold: 'sold', noData: 'No data yet',
    all: 'All', search: 'Search…', searchOrders: 'Number, name or phone', noOrders: 'No orders found',
    customer: 'Customer', recipient: 'Recipient', delivery: 'Delivery', payment: 'Payment', items: 'Items',
    total: 'Total', subtotal: 'Subtotal', deliveryFee: 'Delivery', surprise: 'Surprise gift', cardMessage: 'Card message',
    note: 'Internal note', saveNote: 'Save note', saved: 'Saved', nextStep: 'Next step', cancelOrder: 'Cancel order',
    reopen: 'Reopen', call: 'Call', close: 'Close', paid: 'Paid', pending: 'Pending', cod: 'On delivery',
    demoTag: 'demo',
    addProduct: 'Add product', edit: 'Edit', delete: 'Delete', deleteConfirm: 'Delete this product?',
    hidden: 'Hidden', visible: 'Visible', inStock: 'In stock', soldOut: 'Sold out', price: 'Price', save: 'Save', cancel: 'Cancel',
    brand: 'Brand', category: 'Category', prepTime: 'Prep time (min)', photo: 'Photo', changePhoto: 'Change photo',
    title: 'Name', subtitle: 'Short line', description: 'Description', composition: 'Composition (one per line)',
    careTips: 'Care tips (one per line)', showInShop: 'Show in shop', required: 'Required',
    storageFull: 'Browser storage is full. Pick a smaller photo or reset the demo data.',
    photoHint: 'JPG/PNG, resized automatically', productsCount: 'products', newProduct: 'New product'
  }
};
export type AdminStrings = typeof S.uz;
export const ADMIN_TEXT: Record<Language, AdminStrings> = S;

export const STATUS_LABEL: Record<Language, Record<OrderStatus, string>> = {
  uz: { new: 'Yangi', confirmed: 'Tasdiqlangan', assembling: 'Yig‘ilmoqda', quality_check: 'Tekshiruv', in_transit: 'Yo‘lda', delivered: 'Yetkazildi', cancelled: 'Bekor qilingan' },
  ru: { new: 'Новый', confirmed: 'Подтверждён', assembling: 'Собирается', quality_check: 'Проверка', in_transit: 'В пути', delivered: 'Доставлен', cancelled: 'Отменён' },
  en: { new: 'New', confirmed: 'Confirmed', assembling: 'Assembling', quality_check: 'Quality check', in_transit: 'On the way', delivered: 'Delivered', cancelled: 'Cancelled' }
};

/** Status colours are reserved for status and always shown together with the text label. */
export const STATUS_STYLE: Record<OrderStatus, string> = {
  new: 'bg-amber-400/15 text-amber-300 border-amber-400/40',
  confirmed: 'bg-sky-400/15 text-sky-300 border-sky-400/40',
  assembling: 'bg-violet-400/15 text-violet-300 border-violet-400/40',
  quality_check: 'bg-violet-400/15 text-violet-300 border-violet-400/40',
  in_transit: 'bg-cyan-400/15 text-cyan-300 border-cyan-400/40',
  delivered: 'bg-emerald-400/15 text-emerald-300 border-emerald-400/40',
  cancelled: 'bg-neutral-500/15 text-neutral-400 border-neutral-500/40'
};

export const METHOD_LABEL: Record<PaymentMethod, string> = {
  payme: 'Payme', click: 'Click', uzumpay: 'Uzum Pay', card: 'Humo / Uzcard', cash: 'Naqd / Cash'
};

export const BRAND_LABEL: Record<string, string> = {
  secret_flowers: 'Secret Flowers', secret_berries: 'Secret Berries', green_mood: 'Green Mood', mixed: 'Mixed'
};

export const formatSum = (n: number) => `${Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')} so‘m`;
export const formatShort = (n: number) =>
  n >= 1_000_000 ? `${(n / 1_000_000).toFixed(n >= 10_000_000 ? 0 : 1)} mln` : n >= 1000 ? `${Math.round(n / 1000)} ming` : String(n);

const MONTHS: Record<Language, string[]> = {
  uz: ['yan', 'fev', 'mar', 'apr', 'may', 'iyn', 'iyl', 'avg', 'sen', 'okt', 'noy', 'dek'],
  ru: ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'],
  en: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
};
/** "21 sen, 11:16" — built by hand because browsers lack short Uzbek month names. */
export const formatDateTime = (iso: string, lang: Language) => {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return `${d.getDate()} ${MONTHS[lang][d.getMonth()]}, ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
};
export const dayKey = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
