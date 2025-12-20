
import { Home, ShoppingCart, User, Store } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BottomNavProps {
  cartItemsCount: number;
  currentView: string;
  onNavigate: (view: 'home' | 'cart' | 'profile') => void;
}

export const BottomNav = ({ cartItemsCount, currentView, onNavigate }: BottomNavProps) => {
  const navItems = [
    {
      id: 'home',
      icon: Store,
      label: 'Каталог',
      isActive: ['categories', 'brands', 'products'].includes(currentView),
    },
    {
      id: 'cart' as const,
      icon: ShoppingCart,
      label: 'Корзина',
      isActive: ['cart', 'checkout'].includes(currentView),
      badge: cartItemsCount > 0 ? cartItemsCount : undefined,
    },
    {
      id: 'profile' as const,
      icon: User,
      label: 'Профиль',
      isActive: currentView === 'profile',
    },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-background/95 backdrop-blur-lg border-t border-border shadow-lg">
      <div className="max-w-md mx-auto px-4 py-2">
        <div className="flex items-center justify-around">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id as 'home' | 'cart' | 'profile')}
                className={cn(
                  "relative flex flex-col items-center justify-center gap-1 py-2 px-4 rounded-xl transition-all duration-300",
                  item.isActive
                    ? "text-primary scale-105"
                    : "text-muted-foreground hover:text-foreground hover:scale-105"
                )}
              >
                <div className="relative">
                  <Icon 
                    className={cn(
                      "h-6 w-6 transition-all duration-300",
                      item.isActive && "drop-shadow-[0_0_8px_hsl(var(--primary)/0.5)]"
                    )} 
                  />
                  {item.badge && (
                    <span className="absolute -top-2 -right-2 bg-primary text-primary-foreground rounded-full min-w-5 h-5 px-1.5 flex items-center justify-center text-xs font-bold animate-in zoom-in-50">
                      {item.badge > 99 ? '99+' : item.badge}
                    </span>
                  )}
                </div>
                <span className={cn(
                  "text-xs font-medium transition-all duration-300",
                  item.isActive && "font-semibold"
                )}>
                  {item.label}
                </span>
                {item.isActive && (
                  <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-8 h-1 bg-primary rounded-full animate-in slide-in-from-bottom-2" />
                )}
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
};
