
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { OrderDetail } from '@/types/shop.types';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Package, Calendar, MapPin, Phone, CheckCircle2, XCircle, Clock, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface OrderHistoryPageProps {
  userId: number;
  onBack: () => void;
}

export const OrderHistoryPage = ({ userId, onBack }: OrderHistoryPageProps) => {
  const [orders, setOrders] = useState<OrderDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadOrders = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getUserOrders(userId);
        setOrders(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Не удалось загрузить историю заказов');
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      loadOrders();
    }
  }, [userId]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'confirmed':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'rejected':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'Подтвержден';
      case 'rejected':
        return 'Отклонен';
      default:
        return 'Ожидает';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 px-4">
        <Loader2 className="w-8 h-8 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground">Загрузка истории заказов...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 px-4">
        <p className="text-destructive mb-4">{error}</p>
        <Button onClick={onBack} variant="outline">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Назад
        </Button>
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 px-4">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center py-12 px-6">
            <Package className="h-20 w-20 mb-4 text-muted-foreground opacity-30" />
            <p className="text-muted-foreground mb-6">У вас пока нет заказов</p>
            <Button onClick={onBack} variant="outline">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Назад
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="w-full space-y-4 animate-fade-in">
      <div className="flex items-center gap-4 mb-4">
        <Button onClick={onBack} variant="ghost" size="sm">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Назад
        </Button>
        <h2 className="text-xl font-bold">История заказов</h2>
      </div>

      <div className="space-y-4">
        {orders.map((order) => (
          <Card key={order.id} className="border-border/50 hover:shadow-lg transition-shadow relative">
            {/* Статус заказа в правом верхнем углу рядом с границей */}
            <div className="absolute top-4 right-4 flex items-center gap-2">
              {getStatusIcon(order.status)}
              <span className={cn(
                "text-sm font-medium",
                order.status === 'confirmed' && "text-green-500",
                order.status === 'rejected' && "text-red-500",
                order.status === 'pending' && "text-yellow-500"
              )}>
                {getStatusText(order.status)}
              </span>
            </div>
            <CardContent className="p-4">
              <div className="mb-4 pr-24">
                <div className="flex items-center gap-2 mb-2">
                  <Package className="w-5 h-5 text-primary" />
                  <span className="font-semibold">Заказ #{order.order_id}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Calendar className="w-4 h-4" />
                  {formatDate(order.created_at)}
                </div>
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex items-start gap-2 text-sm">
                  <MapPin className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                  <span className="text-muted-foreground">{order.address}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <Phone className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  <span className="text-muted-foreground">{order.phone}</span>
                </div>
              </div>

              {order.comment && (
                <div className="mb-4 p-3 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground">
                    <span className="font-medium">Комментарий: </span>
                    {order.comment}
                  </p>
                </div>
              )}

              <div className="border-t border-border pt-4">
                <div className="space-y-2 mb-3">
                  {order.items.map((item, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span className="text-muted-foreground">
                        {item.product_name} × {item.quantity}
                      </span>
                      <span className="font-medium">
                        {(item.price * item.quantity).toLocaleString('ru-RU')} ₽
                      </span>
                    </div>
                  ))}
                </div>
                <div className="flex justify-between items-center pt-3 border-t border-border">
                  <span className="font-semibold">Итого:</span>
                  <span className="text-xl font-bold text-primary">
                    {order.total.toLocaleString('ru-RU')} ₽
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

