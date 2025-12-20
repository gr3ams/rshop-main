
import { useState, useEffect } from 'react';
import { CartItem } from '@/types/shop.types';

const CART_STORAGE_KEY = 'cart';

export const useCart = () => {
  const [cart, setCart] = useState<CartItem[]>([]);

  // Загрузка корзины из localStorage при монтировании
  useEffect(() => {
    const loadCart = () => {
      const savedCart = localStorage.getItem(CART_STORAGE_KEY);
      if (savedCart) {
        try {
          setCart(JSON.parse(savedCart));
        } catch (error) {
          console.error('Error loading cart:', error);
          setCart([]);
        }
      }
    };

    // Загружаем корзину при монтировании
    loadCart();

    // Слушаем изменения localStorage из других компонентов/вкладок
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === CART_STORAGE_KEY) {
        loadCart();
      }
    };

    window.addEventListener('storage', handleStorageChange);

    // Также слушаем кастомное событие для изменений в текущей вкладке
    const handleCartChange = () => {
      loadCart();
    };

    window.addEventListener('cartUpdated', handleCartChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('cartUpdated', handleCartChange);
    };
  }, []);

  const saveCart = (newCart: CartItem[]) => {
    setCart(newCart);
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(newCart));
    // Отправляем кастомное событие для синхронизации в текущей вкладке
    window.dispatchEvent(new Event('cartUpdated'));
  };

  const addToCart = (product: Omit<CartItem, 'quantity'>) => {
    const existingItem = cart.find(item => item.id === product.id);
    
    if (existingItem) {
      const updatedCart = cart.map(item =>
        item.id === product.id
          ? { ...item, quantity: item.quantity + 1 }
          : item
      );
      saveCart(updatedCart);
    } else {
      saveCart([...cart, { ...product, quantity: 1 }]);
    }
  };

  const updateCartItem = (productId: number, newQuantity: number) => {
    if (newQuantity <= 0) {
      removeFromCart(productId);
      return;
    }
    
    const updatedCart = cart.map(item =>
      item.id === productId
        ? { ...item, quantity: newQuantity }
        : item
    );
    saveCart(updatedCart);
  };

  const removeFromCart = (productId: number) => {
    const updatedCart = cart.filter(item => item.id !== productId);
    saveCart(updatedCart);
  };

  const clearCart = () => {
    saveCart([]);
  };

  const getCartTotal = () => {
    return cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  };

  const getCartItemsCount = () => {
    return cart.reduce((sum, item) => sum + item.quantity, 0);
  };

  const getCartItem = (productId: number) => {
    return cart.find(item => item.id === productId);
  };

  return {
    cart,
    addToCart,
    updateCartItem,
    removeFromCart,
    clearCart,
    getCartTotal,
    getCartItemsCount,
    getCartItem,
  };
};
