
export interface Category {
  id: number;
  name: string;
}

export interface Brand {
  id: number;
  name: string;
}

export interface Product {
  id: number;
  name: string;
  price: number;
  photo_url?: string;
  description?: string;
  category_id: number;
  brand_id: number;
}

export interface CartItem {
  id: number;
  name: string;
  price: number;
  quantity: number;
  image: string;
  description?: string;
}

export interface OrderData {
  name: string;
  phone: string;
  address: string;
  comment?: string;
  cart: CartItem[];
  total: number;
}

export interface PaymentDetails {
  orderId: string;
  amount: number;
  paymentInfo: string;
  bankDetails?: {
    accountNumber: string;
    bankName: string;
    recipientName: string;
  };
}

export type ViewType = 'categories' | 'brands' | 'products' | 'cart' | 'checkout' | 'payment' | 'profile' | 'orderHistory';

export interface UserProfile {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  orders_count: number;
  total_spent: number;
}

export interface OrderItem {
  product_id: number;
  product_name: string;
  quantity: number;
  price: number;
}

export interface OrderCreate {
  user_id: number;
  user_name: string;
  username?: string;
  phone: string;
  address: string;
  comment?: string;
  items: OrderItem[];
  total: number;
}

export interface OrderDetail {
  id: number;
  order_id: string;
  user_id: number;
  user_name: string;
  phone: string;
  address: string;
  comment?: string;
  total: number;
  status: 'pending' | 'confirmed' | 'rejected';
  created_at: string;
  updated_at: string;
  items: OrderItem[];
}

export interface UserStats {
  user_id: number;
  orders_count: number;
  total_spent: number;
}
