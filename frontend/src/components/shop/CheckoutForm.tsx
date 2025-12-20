
import { useState } from 'react';
import { useCart } from '@/hooks/useCart';
import { useTelegramWebApp } from '@/hooks/useTelegramWebApp';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { ArrowLeft, Check } from 'lucide-react';
import { toast } from 'sonner';

interface CheckoutFormProps {
  onBack: () => void;
  onSuccess: () => void;
}

const PENDING_ORDER_KEY = 'pending_order';

// Валидация российского номера телефона
const validatePhone = (phone: string): boolean => {
  // Удаляем все нецифровые символы
  const cleanPhone = phone.replace(/\D/g, '');
  
  // Проверяем формат: начинается с 7 или 8, затем 10 цифр (итого 11 цифр)
  // Или начинается без 7/8 и имеет 10 цифр
  if (cleanPhone.length === 11) {
    return /^[78]\d{10}$/.test(cleanPhone);
  } else if (cleanPhone.length === 10) {
    return /^\d{10}$/.test(cleanPhone);
  }
  
  return false;
};

// Форматирование телефона для отображения
const formatPhone = (phone: string): string => {
  const cleanPhone = phone.replace(/\D/g, '');
  
  if (cleanPhone.length === 11 && cleanPhone.startsWith('7')) {
    return `+7 (${cleanPhone.slice(1, 4)}) ${cleanPhone.slice(4, 7)}-${cleanPhone.slice(7, 9)}-${cleanPhone.slice(9)}`;
  } else if (cleanPhone.length === 11 && cleanPhone.startsWith('8')) {
    return `+7 (${cleanPhone.slice(1, 4)}) ${cleanPhone.slice(4, 7)}-${cleanPhone.slice(7, 9)}-${cleanPhone.slice(9)}`;
  } else if (cleanPhone.length === 10) {
    return `+7 (${cleanPhone.slice(0, 3)}) ${cleanPhone.slice(3, 6)}-${cleanPhone.slice(6, 8)}-${cleanPhone.slice(8)}`;
  }
  
  return phone;
};

export const CheckoutForm = ({ onBack, onSuccess }: CheckoutFormProps) => {
  const { cart, getCartTotal } = useCart();
  const { user } = useTelegramWebApp();
  const [loading, setLoading] = useState(false);
  const [phoneError, setPhoneError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    address: '',
    comment: '',
  });

  const total = getCartTotal();

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value;
    
    // Разрешаем ввод только цифр, +, -, (, ), пробелов
    value = value.replace(/[^\d+\-() ]/g, '');
    
    setFormData({
      ...formData,
      phone: value,
    });
    
    // Очищаем ошибку при вводе
    if (phoneError) {
      setPhoneError(null);
    }
  };

  const handlePhoneBlur = () => {
    if (formData.phone.trim()) {
      if (!validatePhone(formData.phone)) {
        setPhoneError('Введите корректный номер телефона (например: +7 (999) 123-45-67)');
      } else {
        // Форматируем телефон при потере фокуса
        const formatted = formatPhone(formData.phone);
        setFormData({
          ...formData,
          phone: formatted,
        });
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Проверяем наличие пользователя
    if (!user?.id) {
      toast.error('Ошибка: не удалось определить пользователя. Пожалуйста, откройте приложение через Telegram.');
      return;
    }
    
    if (cart.length === 0) {
      toast.error('Корзина пуста');
      return;
    }
    
    // Валидация телефона
    if (!validatePhone(formData.phone)) {
      setPhoneError('Введите корректный номер телефона (например: +7 (999) 123-45-67)');
      return;
    }
    
    setLoading(true);

    try {
      const userId = typeof user.id === 'string' ? parseInt(user.id, 10) : user.id;
      
      if (!userId || userId <= 0) {
        throw new Error('Invalid user ID');
      }

      // Сохраняем данные заказа в localStorage (не создаем заказ в БД)
      const pendingOrder = {
        user_id: userId,
        user_name: formData.name,
        username: user.username || undefined,  // Username пользователя в Telegram
        phone: formData.phone,
        address: formData.address,
        comment: formData.comment || undefined,
        items: cart.map(item => ({
          product_id: item.id,
          product_name: item.name,
          quantity: item.quantity,
          price: item.price,
        })),
        total: total,
        timestamp: Date.now(),
      };

      localStorage.setItem(PENDING_ORDER_KEY, JSON.stringify(pendingOrder));

      toast.success('Данные сохранены. Переход к оплате...');
      onSuccess();
    } catch (error) {
      console.error('Error saving order data:', error);
      toast.error('Ошибка при сохранении данных');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (e.target.name === 'phone') {
      handlePhoneChange(e as React.ChangeEvent<HTMLInputElement>);
    } else {
      setFormData({
        ...formData,
        [e.target.name]: e.target.value,
      });
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold">Оформление заказа</h2>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="space-y-2">
          <Label htmlFor="name">Ваше имя</Label>
          <Input
            id="name"
            name="name"
            type="text"
            required
            value={formData.name}
            onChange={handleChange}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="phone">Телефон *</Label>
          <Input
            id="phone"
            name="phone"
            type="tel"
            required
            placeholder="+7 (999) 123-45-67"
            value={formData.phone}
            onChange={handleChange}
            onBlur={handlePhoneBlur}
            className={phoneError ? 'border-destructive' : ''}
          />
          {phoneError && (
            <p className="text-sm text-destructive">{phoneError}</p>
          )}
          <p className="text-xs text-muted-foreground">
            Формат: +7 (999) 123-45-67 или 8 (999) 123-45-67
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="address">Адрес доставки</Label>
          <Input
            id="address"
            name="address"
            type="text"
            required
            value={formData.address}
            onChange={handleChange}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="comment">Комментарий к заказу</Label>
          <Textarea
            id="comment"
            name="comment"
            rows={3}
            value={formData.comment}
            onChange={handleChange}
          />
        </div>

        <Card className="mt-4">
          <CardContent className="p-4">
            <div className="flex justify-between font-bold text-lg text-primary">
              <span>Итого:</span>
              <span>{total.toLocaleString('ru-RU')} ₽</span>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-3 mt-2">
          <Button type="button" variant="outline" onClick={onBack} className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Вернуться в корзину
          </Button>
          <Button type="submit" disabled={loading} className="gap-2">
            <Check className="h-4 w-4" />
            {loading ? 'Сохранение...' : 'Перейти к оплате'}
          </Button>
        </div>
      </form>
    </div>
  );
};

export { PENDING_ORDER_KEY };
