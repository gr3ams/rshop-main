
import { Package, MessageCircle, Globe, LogOut, User, ShoppingBag, TrendingUp, Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from './ThemeToggle';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
import { TELEGRAM_CONFIG } from '@/config/app.config';
import { useState, useEffect } from 'react';

interface ProfilePageProps {
  user: {
    id: number;
    first_name: string;
    last_name?: string;
    username?: string;
  } | null;
  onClose: () => void;
  onShowOrderHistory?: () => void;
}

export const ProfilePage = ({ user, onClose, onShowOrderHistory }: ProfilePageProps) => {
  const [stats, setStats] = useState({
    orders_count: 0,
    total_spent: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      if (user?.id) {
        try {
          setLoading(true);
          const data = await api.getUserStats(user.id);
          setStats({
            orders_count: data.orders_count,
            total_spent: data.total_spent,
          });
        } catch (error) {
          console.error('Failed to load user stats:', error);
        } finally {
          setLoading(false);
        }
      }
    };

    loadStats();
  }, [user?.id]);

  const handleSupportClick = () => {
    const supportUsername = TELEGRAM_CONFIG.supportUsername;
    if (supportUsername) {
      // Открываем чат с поддержкой в Telegram
      const supportUrl = `https://t.me/${supportUsername.replace('@', '')}`;
      
      // Используем Telegram WebApp API для открытия ссылки
      if (window.Telegram?.WebApp) {
        window.Telegram.WebApp.openTelegramLink(supportUrl);
      } else {
        // Fallback для случаев вне Telegram
        window.open(supportUrl, '_blank');
      }
    }
  };

  const menuItems = [
    {
      icon: MessageCircle,
      title: 'Поддержка',
      description: 'Связаться с нами',
      onClick: handleSupportClick,
    },
    {
      icon: Package,
      title: 'История заказов',
      description: 'Просмотр всех ваших заказов',
      onClick: () => {
        if (onShowOrderHistory) {
          onShowOrderHistory();
        }
      },
    },
  ];

  const settingsItems: never[] = [];

  const displayName = user
    ? `${user.first_name}${user.last_name ? ' ' + user.last_name : ''}`
    : 'Гость';

  return (
    <div className="w-full space-y-6 animate-fade-in">
      {/* User Profile Card */}
      <Card className="relative overflow-hidden border-border/50 bg-gradient-to-br from-primary/10 via-background to-background">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent" />
        <CardContent className="relative p-6">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center shadow-lg ring-4 ring-background">
                <User className="w-10 h-10 text-primary-foreground" />
              </div>
              <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-500 rounded-full border-4 border-background" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-2xl font-bold text-foreground truncate">
                {displayName}
              </h2>
              {user?.username && (
                <p className="text-sm text-muted-foreground truncate">
                  @{user.username}
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Statistics */}
      <div className="grid grid-cols-2 gap-4">
        <Card className="border-border/50 bg-gradient-to-br from-primary/5 to-background hover:shadow-lg transition-all duration-300 hover:scale-105">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <ShoppingBag className="w-6 h-6 text-primary" />
              </div>
              <div>
                {loading ? (
                  <Loader2 className="w-6 h-6 animate-spin text-primary" />
                ) : (
                  <p className="text-2xl font-bold text-foreground">{stats.orders_count}</p>
                )}
                <p className="text-xs text-muted-foreground">Заказов</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/50 bg-gradient-to-br from-primary/5 to-background hover:shadow-lg transition-all duration-300 hover:scale-105">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-primary" />
              </div>
              <div>
                {loading ? (
                  <Loader2 className="w-6 h-6 animate-spin text-primary" />
                ) : (
                  <p className="text-2xl font-bold text-foreground">
                    {stats.total_spent.toLocaleString('ru-RU')}₽
                  </p>
                )}
                <p className="text-xs text-muted-foreground">Потрачено</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Menu Items */}
      <Card className="border-border/50">
        <CardContent className="p-4 space-y-2">
          <h3 className="text-sm font-semibold text-muted-foreground mb-3 px-2">
            ФУНКЦИИ
          </h3>
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.title}
                onClick={item.onClick}
                className={cn(
                  "w-full flex items-center gap-4 p-3 rounded-xl transition-all duration-300",
                  "hover:bg-primary/10 hover:scale-[1.02] active:scale-[0.98]",
                  "group"
                )}
              >
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                  <Icon className="w-5 h-5 text-primary" />
                </div>
                <div className="flex-1 text-left">
                  <p className="font-medium text-foreground">{item.title}</p>
                  <p className="text-xs text-muted-foreground">{item.description}</p>
                </div>
              </button>
            );
          })}
        </CardContent>
      </Card>

      {/* Settings */}
      <Card className="border-border/50">
        <CardContent className="p-4 space-y-2">
          <h3 className="text-sm font-semibold text-muted-foreground mb-3 px-2">
            НАСТРОЙКИ
          </h3>
          
          {/* Theme Toggle */}
          <div className="flex items-center justify-between p-3 rounded-xl hover:bg-primary/10 transition-colors">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Globe className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="font-medium text-foreground">Тема</p>
                <p className="text-xs text-muted-foreground">Светлая / Темная</p>
              </div>
            </div>
            <ThemeToggle />
          </div>
        </CardContent>
      </Card>

      {/* Close App Button */}
      <Button
        onClick={onClose}
        variant="destructive"
        size="lg"
        className="w-full gap-2 shadow-lg hover:shadow-xl transition-all duration-300"
      >
        <LogOut className="w-5 h-5" />
        Закрыть приложение
      </Button>
    </div>
  );
};
