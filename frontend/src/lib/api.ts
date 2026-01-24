import { API_ENDPOINTS } from "@/config/app.config";
import {
  Brand,
  Category,
  OrderCreate,
  OrderDetail,
  PaymentDetails,
  Product,
  UserStats,
} from "@/types/shop.types";

const fetchJSON = async <T>(url: string, options?: RequestInit): Promise<T> => {
  const response = await fetch(url, {
    headers: {
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Ошибка запроса");
  }

  return response.json() as Promise<T>;
};

export const api = {
  // Каталог
  getAllProducts: () => fetchJSON<Product[]>(API_ENDPOINTS.allProducts),
  getCategories: () => fetchJSON<Category[]>(API_ENDPOINTS.categories),
  getBrands: (categoryId: number) =>
    fetchJSON<Brand[]>(API_ENDPOINTS.brands(categoryId)),

  // Админ данные
  getAdminData: () => fetchJSON<{ brands: Brand[]; categories: Category[] }>(API_ENDPOINTS.admin.data),
  addProduct: (data: FormData) =>
    fetchJSON<{ success: boolean; message: string; product_id: number }>(API_ENDPOINTS.admin.addProduct, {
      method: "POST",
      body: data,
    }),

  // Заказы
  createOrder: (order: OrderCreate) =>
    fetchJSON<{ success: boolean; order_id: string; message: string }>(API_ENDPOINTS.orders.create, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(order),
    }),
  getUserOrders: (userId: number) =>
    fetchJSON<OrderDetail[]>(API_ENDPOINTS.user.orders(userId)),
  getUserStats: (userId: number) =>
    fetchJSON<UserStats>(API_ENDPOINTS.user.stats(userId)),

  // Оплата
  getPaymentDetails: (orderId: string) =>
    fetchJSON<PaymentDetails>(`${API_ENDPOINTS.payment.details}?orderId=${orderId}`),
  cancelOrder: (orderId: string) =>
    fetchJSON<{ success: boolean; message: string }>(API_ENDPOINTS.payment.cancel, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ orderId }),
    }),
};

