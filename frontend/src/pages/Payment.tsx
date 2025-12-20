
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, XCircle, Copy } from 'lucide-react';
import { api } from '@/lib/api';
import { PaymentDetails } from '@/types/shop.types';
import { LoadingSpinner } from '@/components/shop/LoadingSpinner';
import { ErrorMessage } from '@/components/shop/ErrorMessage';
import { toast } from 'sonner';
import { PENDING_ORDER_KEY } from '@/components/shop/CheckoutForm';
import { useCart } from '@/hooks/useCart';

export const Payment = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { clearCart } = useCart();
  const orderId = searchParams.get('orderId');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [paymentDetails, setPaymentDetails] = useState<PaymentDetails | null>(null);
  const [processing, setProcessing] = useState(false);
  const [orderCreated, setOrderCreated] = useState(false);

  useEffect(() => {
    // Если нет orderId в URL, проверяем localStorage
    if (!orderId) {
      const pendingOrder = localStorage.getItem(PENDING_ORDER_KEY);
      if (pendingOrder) {
        try {
          const orderData = JSON.parse(pendingOrder);
          // Если заказ еще не создан в БД, создаем его сразу для получения orderId
          // Но показываем страницу оплаты
          loadPaymentDetailsFromPending(orderData);
        } catch (err) {
          console.error('Error parsing pending order:', err);
          setError('Ошибка при загрузке данных заказа');
          setLoading(false);
        }
      } else {
        // Нет ни orderId, ни pending_order - перенаправляем на главную
        navigate('/');
      }
    } else {
      // Есть orderId - загружаем детали оплаты
      loadPaymentDetails();
    }
  }, [orderId, navigate]);

  const loadPaymentDetailsFromPending = async (pendingOrder: any) => {
    try {
      setLoading(true);
      
      // Создаем временный orderId для отображения
      // Реальный заказ создастся при нажатии "Я оплатил"
      const tempOrderId = `TEMP_${Date.now()}`;
      
      setPaymentDetails({
        orderId: tempOrderId,
        amount: pendingOrder.total,
        paymentInfo: `Оплата заказа\nСумма: ${pendingOrder.total} ₽\n\nПосле оплаты нажмите "Я оплатил" для подтверждения.`,
        bankDetails: {
          accountNumber: "40817810099910004312",
          bankName: "Тинькофф Банк",
          recipientName: "ИП Иванов Иван Иванович"
        }
      });
      
      // Сохраняем данные pending_order в состояние компонента
      (window as any).__pendingOrderData__ = pendingOrder;
      
    } catch (err) {
      setError('Не удалось загрузить данные оплаты');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadPaymentDetails = async () => {
    if (!orderId) return;

    try {
      setLoading(true);
      const data = await api.getPaymentDetails(orderId);
      setPaymentDetails(data);
      setOrderCreated(true); // Заказ уже создан в БД
    } catch (err) {
      setError('Не удалось загрузить данные оплаты');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const createOrderAndConfirm = async () => {
    const pendingOrder = (window as any).__pendingOrderData__ || 
                         JSON.parse(localStorage.getItem(PENDING_ORDER_KEY) || 'null');
    
    if (!pendingOrder) {
      toast.error('Ошибка: данные заказа не найдены');
      return;
    }

    try {
      setProcessing(true);
      
      // Создаем заказ в БД со статусом "на подтверждении" (PENDING)
      const response = await api.createOrder({
        user_id: pendingOrder.user_id,
        user_name: pendingOrder.user_name,
        username: pendingOrder.username,  // Username пользователя в Telegram
        phone: pendingOrder.phone,
        address: pendingOrder.address,
        comment: pendingOrder.comment,
        items: pendingOrder.items,
        total: pendingOrder.total,
      });

      // Удаляем pending_order из localStorage
      localStorage.removeItem(PENDING_ORDER_KEY);
      delete (window as any).__pendingOrderData__;

      // Очищаем корзину после создания заказа
      clearCart();

      toast.success('Заказ создан! Мы проверим оплату и свяжемся с вами.');
      setTimeout(() => navigate('/'), 2000);
    } catch (err) {
      console.error('Error creating order:', err);
      toast.error('Ошибка при создании заказа');
    } finally {
      setProcessing(false);
    }
  };

  const handleConfirmPayment = async () => {
    if (orderCreated && orderId) {
      // Заказ уже создан, ничего не делаем (подтверждение происходит в чате админов)
      toast.info('Заказ уже создан и ожидает подтверждения.');
      return;
    } else {
      // Заказ еще не создан, создаем его со статусом PENDING
      await createOrderAndConfirm();
    }
  };

  const handleCancelOrder = async () => {
    if (!orderId) {
      // Просто удаляем pending_order и возвращаемся
      localStorage.removeItem(PENDING_ORDER_KEY);
      delete (window as any).__pendingOrderData__;
      toast.success('Заказ отменен');
      navigate('/');
      return;
    }

    try {
      setProcessing(true);
      await api.cancelOrder(orderId);
      localStorage.removeItem(PENDING_ORDER_KEY);
      toast.success('Заказ отменен');
      navigate('/');
    } catch (err) {
      console.error('Error canceling order:', err);
      toast.error('Ошибка отмены заказа');
    } finally {
      setProcessing(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Скопировано в буфер обмена');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !paymentDetails) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <ErrorMessage message={error || 'Данные не найдены'} onRetry={() => navigate('/')} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="max-w-2xl mx-auto py-8">
        <Card>
          <CardHeader>
            <CardTitle className="text-center text-2xl">
              Оплата заказа
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Order Info */}
            <div className="bg-muted/50 rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-muted-foreground">Сумма к оплате:</span>
                <span className="text-2xl font-bold text-primary">
                  {paymentDetails.amount.toLocaleString('ru-RU')} ₽
                </span>
              </div>
              {paymentDetails.orderId && !paymentDetails.orderId.startsWith('TEMP_') && (
                <div className="flex justify-between items-center mt-2">
                  <span className="text-muted-foreground">Номер заказа:</span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-semibold">{paymentDetails.orderId}</span>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => copyToClipboard(paymentDetails.orderId)}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </div>

            {/* Payment Info */}
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Информация об оплате</h3>
                <div className="bg-muted/50 rounded-lg p-4 whitespace-pre-line">
                  {paymentDetails.paymentInfo}
                </div>
              </div>

              {paymentDetails.bankDetails && (
                <div>
                  <h3 className="font-semibold mb-2">Банковские реквизиты</h3>
                  <Card>
                    <CardContent className="p-4 space-y-2">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Получатель:</span>
                        <span className="font-medium">{paymentDetails.bankDetails.recipientName}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Банк:</span>
                        <span className="font-medium">{paymentDetails.bankDetails.bankName}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-muted-foreground">Счет:</span>
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-medium">{paymentDetails.bankDetails.accountNumber}</span>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => copyToClipboard(paymentDetails.bankDetails!.accountNumber)}
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex flex-col gap-3 pt-4">
              <Button
                onClick={handleConfirmPayment}
                disabled={processing}
                className="w-full gap-2"
                size="lg"
              >
                <CheckCircle className="h-5 w-5" />
                {processing ? 'Обработка...' : 'Я оплатил'}
              </Button>
              <Button
                onClick={handleCancelOrder}
                disabled={processing}
                variant="outline"
                className="w-full gap-2"
              >
                <XCircle className="h-5 w-5" />
                Отменить заказ
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
