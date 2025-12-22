
// Режимы работы приложения
export type AppMode = 'production' | 'debug-user' | 'debug-admin';

// Текущий режим работы (измените здесь для переключения режимов)
let APP_MODE: AppMode = 'production';
export { APP_MODE };

// Конфигурация режимов
export const MODE_CONFIG = {
  production: {
    checkTelegram: true,
    requireTelegram: true,
    role: 'user', // роль определяется по telegram ID
  },
  'debug-user': {
    checkTelegram: false,
    requireTelegram: false,
    role: 'user',
  },
  'debug-admin': {
    checkTelegram: false,
    requireTelegram: false,
    role: 'admin',
  },
} as const;

// API эндпоинты
export const API_ENDPOINTS = {
  categories: '/api/categories',
  brands: (categoryId: number) => `/api/brands/${categoryId}`,
  products: (brandId: number) => `/api/products/${brandId}`,
  allProducts: '/api/products',
  orders: {
    create: '/api/orders/create',
  },
  payment: {
    details: '/api/payment/details',
    confirm: '/api/payment/confirm',
    cancel: '/api/payment/cancel',
  },
  admin: {
    data: '/api/admin/data',
    addProduct: '/api/admin/add_product',
  },
  user: {
    orders: (userId: number) => `/api/orders/user/${userId}`,
    stats: (userId: number) => `/api/user/${userId}/stats`,
  },
} as const;

// Telegram конфигурация
export const TELEGRAM_CONFIG = {
  botToken: '3892212196:AAHKC4hN1Zcmdqf9R4ZR1myaQYlSkMcewkQ',
  adminIds: [6326719341, 790410251, 6388614116, 8188457128, 859330334] as number[],
  supportUsername: 'support', // Замените на реальный username саппорта
};

export const STORE_LINK = 'https://rshop1.ru';

// Изображения
export const IMAGES = {
  background: '/template.jpg',
  backgroundDark: '/template-dark.jpg',
  placeholder: 'https://cdn-icons-png.flaticon.com/512/1178/1178479.png',
} as const;

// Получить текущую конфигурацию режима
export const getCurrentModeConfig = () => MODE_CONFIG[APP_MODE];

// Проверка является ли пользователь админом
export const isAdmin = (telegramId?: number): boolean => {
  const config = getCurrentModeConfig();
  
  // В режиме debug-admin всегда админ
  if (APP_MODE === 'debug-admin') {
    return true;
  }
  
  if (!telegramId) {
    return false;
  }
  
  return TELEGRAM_CONFIG.adminIds.includes(telegramId);
};
