
import { useState, useEffect, useMemo } from 'react';
import { useTelegramWebApp } from '@/hooks/useTelegramWebApp';
import { useCart } from '@/hooks/useCart';
import { api } from '@/lib/api';
import { Brand, Category, Product, ViewType } from '@/types/shop.types';
import { BottomNav } from '@/components/shop/BottomNav';
import { ThemeToggle } from '@/components/shop/ThemeToggle';
import { SearchFilter } from '@/components/shop/SearchFilter';
import { LoadingSpinner } from '@/components/shop/LoadingSpinner';
import { ErrorMessage } from '@/components/shop/ErrorMessage';
import { ProductsList } from '@/components/shop/ProductsList';
import { CartPage } from '@/components/shop/CartPage';
import { CheckoutForm } from '@/components/shop/CheckoutForm';
import { ProfilePage } from '@/components/shop/ProfilePage';
import { OrderHistoryPage } from '@/components/shop/OrderHistoryPage';
import { useNavigate } from 'react-router-dom';
import { IMAGES } from '@/config/app.config';

interface FilterState {
  categoryId: number | null;
  brandId: number | null;
  searchText: string;
  minPrice: number | null;
  maxPrice: number | null;
}

export const Shop = () => {
  const { isReady, user, close } = useTelegramWebApp();
  const { cart, clearCart } = useCart();
  const navigate = useNavigate();
  
  // Вычисляем количество товаров в корзине для реактивного обновления
  const cartItemsCount = cart.reduce((sum, item) => sum + item.quantity, 0);
  
  const [currentView, setCurrentView] = useState<ViewType>('products');
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [filteredProducts, setFilteredProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [allBrands, setAllBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterState>({
    categoryId: null,
    brandId: null,
    searchText: '',
    minPrice: null,
    maxPrice: null,
  });

  useEffect(() => {
    if (isReady) {
      loadAllData();
    }
  }, [isReady]);

  const loadAllData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Загружаем все данные параллельно
      const [productsData, categoriesData] = await Promise.all([
        api.getAllProducts(),
        api.getCategories(),
      ]);

      setAllProducts(productsData);
      setCategories(categoriesData);

      // Загружаем все бренды для фильтров (убираем дубликаты)
      const allBrandsData: Brand[] = [];
      const seenBrandIds = new Set<number>();
      for (const cat of categoriesData) {
        const catBrands = await api.getBrands(cat.id);
        for (const brand of catBrands) {
          if (!seenBrandIds.has(brand.id)) {
            seenBrandIds.add(brand.id);
            allBrandsData.push(brand);
          }
        }
      }
      setAllBrands(allBrandsData);
      
      // Применяем фильтры к загруженным товарам
      applyFilters(productsData, filters);
    } catch (error) {
      setError('Не удалось загрузить данные. Пожалуйста, попробуйте позже.');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = (products: Product[], filterState: FilterState) => {
    let filtered = [...products];

    // Фильтр по категории (теперь категории уникальны по имени)
    if (filterState.categoryId) {
      filtered = filtered.filter((p) => p.category_id === filterState.categoryId);
    }

    // Фильтр по бренду (через brand_id категории)
    if (filterState.brandId) {
      const categoryIdsForBrand = categories
        .filter((c) => c.brand_id === filterState.brandId)
        .map((c) => c.id);
      
      if (categoryIdsForBrand.length > 0) {
        filtered = filtered.filter((p) => categoryIdsForBrand.includes(p.category_id));
      } else {
        // Если нет категорий для этого бренда, показываем пустой список
        filtered = [];
      }
    }

    // Фильтр по тексту поиска
    if (filterState.searchText) {
      const searchLower = filterState.searchText.toLowerCase();
      filtered = filtered.filter((p) =>
        p.name.toLowerCase().includes(searchLower)
      );
    }

    // Фильтр по цене
    if (filterState.minPrice !== null) {
      filtered = filtered.filter((p) => p.price >= filterState.minPrice!);
    }
    if (filterState.maxPrice !== null) {
      filtered = filtered.filter((p) => p.price <= filterState.maxPrice!);
    }

    setFilteredProducts(filtered);
  };

  useEffect(() => {
    if (allProducts.length > 0) {
      applyFilters(allProducts, filters);
    }
  }, [filters, allProducts, categories, allBrands]);

  const handleFilter = (newFilters: FilterState) => {
    setFilters(newFilters);
  };

  const showCartPage = () => {
    setCurrentView('cart');
  };

  const showCheckoutPage = () => {
    setCurrentView('checkout');
  };

  const showPaymentPage = () => {
    navigate('/payment');
  };

  const handleSidebarNavigate = (view: 'home' | 'cart' | 'profile') => {
    if (view === 'home') {
      setCurrentView('products');
      loadAllData();
    } else if (view === 'cart') {
      showCartPage();
    } else if (view === 'profile') {
      setCurrentView('profile');
    }
  };

  const getPageTitle = () => {
    switch (currentView) {
      case 'products':
        return 'Каталог товаров';
      case 'cart':
        return 'Корзина';
      case 'checkout':
        return 'Оформление заказа';
      case 'profile':
        return 'Профиль';
      case 'orderHistory':
        return 'История заказов';
      default:
        return 'Каталог товаров';
    }
  };

  const renderContent = () => {
    if (loading) {
      return <LoadingSpinner />;
    }

    if (error) {
      return <ErrorMessage message={error} onRetry={loadAllData} />;
    }

    switch (currentView) {
      case 'products':
        return (
          <>
            <SearchFilter
              categories={categories}
              brands={allBrands}
              onFilter={handleFilter}
            />
            <ProductsList 
              products={filteredProducts} 
              categoryName=""
            />
          </>
        );
      case 'cart':
        return <CartPage onContinueShopping={() => setCurrentView('products')} onCheckout={showCheckoutPage} />;
      case 'checkout':
        return <CheckoutForm onBack={showCartPage} onSuccess={() => navigate('/payment')} />;
      case 'profile':
        return (
          <ProfilePage 
            user={user} 
            onClose={close}
            onShowOrderHistory={() => setCurrentView('orderHistory')}
          />
        );
      case 'orderHistory':
        return (
          <OrderHistoryPage 
            userId={user?.id || 0}
            onBack={() => setCurrentView('profile')}
          />
        );
      default:
        return null;
    }
  };

  if (!isReady) {
    return <LoadingSpinner />;
  }

  return (
    <div className="min-h-screen w-full">
      {/* Header */}
      <div className="sticky top-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
        <div className="flex items-center justify-between px-4 py-3">
          <h1 className="text-xl font-bold">{getPageTitle()}</h1>
          <div className="flex items-center gap-2">
            <ThemeToggle />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 pb-24">
        {renderContent()}
      </div>

      {/* Bottom Navigation */}
      <BottomNav
        cartItemsCount={cartItemsCount}
        currentView={currentView}
        onNavigate={handleSidebarNavigate}
      />
    </div>
  );
};
