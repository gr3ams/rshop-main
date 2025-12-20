
import { useCart } from '@/hooks/useCart';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { ShoppingCart, ArrowLeft, CreditCard, Plus, Minus, Trash2, Store } from 'lucide-react';
import { IMAGES } from '@/config/app.config';
import { toast } from 'sonner';
import { useState } from 'react';

interface CartPageProps {
  onContinueShopping: () => void;
  onCheckout: () => void;
}

export const CartPage = ({ onContinueShopping, onCheckout }: CartPageProps) => {
  const { cart, updateCartItem, removeFromCart, getCartTotal, getCartItemsCount } = useCart();
  const total = getCartTotal();
  const [deleteConfirm, setDeleteConfirm] = useState<{ open: boolean; productId: number | null; productName: string }>({
    open: false,
    productId: null,
    productName: '',
  });

  const handleUpdateQuantity = (productId: number, productName: string, newQuantity: number) => {
    if (newQuantity <= 0) {
      // Показываем подтверждение при попытке удалить через уменьшение количества
      setDeleteConfirm({ open: true, productId, productName });
    } else {
      updateCartItem(productId, newQuantity);
      toast.success(`Количество "${productName}" изменено на ${newQuantity}`);
    }
  };

  const handleRemoveClick = (productId: number, productName: string) => {
    setDeleteConfirm({ open: true, productId, productName });
  };

  const handleConfirmRemove = () => {
    if (deleteConfirm.productId !== null) {
      removeFromCart(deleteConfirm.productId);
      toast.success(`${deleteConfirm.productName} удален из корзины`);
      setDeleteConfirm({ open: false, productId: null, productName: '' });
    }
  };

  if (cart.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 px-4">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center py-12 px-6">
            <ShoppingCart className="h-20 w-20 mb-4 text-muted-foreground opacity-30" />
            <p className="text-muted-foreground mb-6">Ваша корзина пуста</p>
            <Button onClick={onContinueShopping} className="gap-2">
              <Store className="h-4 w-4" />
              В каталог товаров
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 px-4 pb-4 w-full max-w-full overflow-x-hidden" style={{ maxWidth: '100vw', boxSizing: 'border-box' }}>
      <h2 className="text-lg font-semibold">Ваша корзина</h2>

      <div className="flex flex-col gap-3 w-full max-w-full">
        {cart.map((item) => (
          <Card key={item.id} className="w-full" style={{ maxWidth: '100%', overflow: 'hidden' }}>
            <CardContent className="p-3 flex gap-2.5 items-center w-full" style={{ maxWidth: '100%', overflow: 'hidden', boxSizing: 'border-box' }}>
              {/* Фиксированный размер изображения - 60x60px */}
              <div 
                className="w-[60px] h-[60px] rounded-lg flex-shrink-0 relative overflow-hidden product-image-container"
                style={{ 
                  width: '60px', 
                  height: '60px', 
                  minWidth: '60px', 
                  minHeight: '60px',
                }}
              >
                <img
                  src={item.image}
                  alt={item.name}
                  className="absolute inset-0 w-full h-full object-cover"
                  onError={(e) => {
                    e.currentTarget.src = IMAGES.placeholder;
                  }}
                />
              </div>

              <div className="flex-1 min-w-0 overflow-hidden">
                <div className="font-semibold truncate text-sm">{item.name}</div>
                <div className="text-xs text-muted-foreground">
                  {item.price.toLocaleString('ru-RU')} ₽ за шт.
                </div>
                <div className="font-semibold text-primary mt-1 text-sm">
                  {(item.price * item.quantity).toLocaleString('ru-RU')} ₽
                </div>
              </div>

              <div className="flex flex-col items-end gap-2 flex-shrink-0">
                <div className="flex items-center border border-border rounded-full overflow-hidden">
                  <button
                    className="bg-muted hover:bg-muted/80 w-7 h-7 flex items-center justify-center font-semibold"
                    onClick={() => handleUpdateQuantity(item.id, item.name, item.quantity - 1)}
                  >
                    <Minus className="h-3 w-3" />
                  </button>
                  <span className="px-2 text-sm font-medium min-w-[24px] text-center">
                    {item.quantity}
                  </span>
                  <button
                    className="bg-muted hover:bg-muted/80 w-7 h-7 flex items-center justify-center font-semibold"
                    onClick={() => handleUpdateQuantity(item.id, item.name, item.quantity + 1)}
                  >
                    <Plus className="h-3 w-3" />
                  </button>
                </div>
                <button
                  className="text-destructive hover:text-destructive/80 p-1.5"
                  onClick={() => handleRemoveClick(item.id, item.name)}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="w-full mt-2">
        <CardContent className="p-4">
          <div className="flex justify-between items-center mb-4">
            <span className="text-lg font-semibold">Итого:</span>
            <span className="text-xl font-bold text-primary">
              {total.toLocaleString('ru-RU')} ₽
            </span>
          </div>
          <Button onClick={onCheckout} className="w-full gap-2" size="lg">
            <CreditCard className="h-4 w-4" />
            Оформить заказ
          </Button>
        </CardContent>
      </Card>

      <AlertDialog open={deleteConfirm.open} onOpenChange={(open) => setDeleteConfirm({ ...deleteConfirm, open })}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить товар из корзины?</AlertDialogTitle>
            <AlertDialogDescription>
              Вы уверены, что хотите удалить "{deleteConfirm.productName}" из корзины? Это действие нельзя отменить.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmRemove} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Удалить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
