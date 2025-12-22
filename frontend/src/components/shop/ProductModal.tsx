
import { Product } from '@/types/shop.types';
import { useCart } from '@/hooks/useCart';
import { Dialog, DialogContent, DialogClose } from '@/components/ui/dialog';
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
import { Button } from '@/components/ui/button';
import { X, ShoppingCart, Trash2, Plus, Minus, ZoomIn } from 'lucide-react';
import { IMAGES } from '@/config/app.config';
import { toast } from 'sonner';
import { useState, useEffect } from 'react';
import { Skeleton } from '@/components/ui/skeleton';

interface ProductModalProps {
  product: Product;
  onClose: () => void;
}

export const ProductModal = ({ product, onClose }: ProductModalProps) => {
  const { addToCart, updateCartItem, removeFromCart, getCartItem } = useCart();
  const cartItem = getCartItem(product.id);
  const [showZoom, setShowZoom] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageDimensions, setImageDimensions] = useState<{ width: number; height: number } | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  const photoUrl = product.photo_url
    ? `/static/${product.photo_url}`
    : IMAGES.placeholder;

  // Сбрасываем состояние загрузки при изменении товара
  useEffect(() => {
    setImageLoaded(false);
    setImageDimensions(null);
    
    // Предзагружаем изображение для получения размеров
    const img = new Image();
    img.onload = () => {
      setImageDimensions({
        width: img.naturalWidth,
        height: img.naturalHeight
      });
    };
    img.src = photoUrl;
  }, [product.id, photoUrl]);

  const handleAddToCart = () => {
    addToCart({
      id: product.id,
      name: product.name,
      price: product.price,
      image: photoUrl,
      description: product.description,
    });
    toast.success(`${product.name} добавлен в корзину`);
  };

  const handleUpdateQuantity = (newQuantity: number) => {
    if (newQuantity <= 0) {
      // Показываем подтверждение при попытке удалить через уменьшение количества
      setDeleteConfirm(true);
    } else {
      updateCartItem(product.id, newQuantity);
      toast.success(`Количество "${product.name}" изменено на ${newQuantity}`);
    }
  };

  const handleRemoveClick = () => {
    setDeleteConfirm(true);
  };

  const handleConfirmRemove = () => {
    removeFromCart(product.id);
    toast.success(`${product.name} удален из корзины`);
    setDeleteConfirm(false);
    onClose();
  };

  return (
    <>
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto p-5">
          <DialogClose className="absolute top-4 right-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100">
            <X className="h-4 w-4" />
            <span className="sr-only">Close</span>
          </DialogClose>

          <div
            className="w-full flex items-center justify-center overflow-hidden rounded-lg cursor-zoom-in mb-5 relative bg-muted"
            style={{
              minHeight: imageDimensions 
                ? `${Math.min(400, (imageDimensions.height / imageDimensions.width) * 100)}px`
                : '250px',
              aspectRatio: imageDimensions 
                ? `${imageDimensions.width} / ${imageDimensions.height}`
                : '4 / 3'
            }}
            onClick={() => setShowZoom(true)}
            onDoubleClick={(e) => {
              e.stopPropagation();
              setShowZoom(true);
            }}
          >
            {/* Skeleton placeholder пока изображение загружается */}
            {!imageLoaded && (
              <Skeleton className="absolute inset-0 w-full h-full rounded-lg" />
            )}
            
            <img
              src={photoUrl}
              alt={product.name}
              className={`w-full h-full max-w-full max-h-[400px] object-contain rounded-lg transition-opacity duration-300 ${
                imageLoaded ? 'opacity-100' : 'opacity-0'
              }`}
              style={{ 
                maxHeight: '400px',
                objectFit: 'contain'
              }}
              onLoad={() => setImageLoaded(true)}
              onError={(e) => {
                e.currentTarget.src = IMAGES.placeholder;
                setImageLoaded(true);
              }}
            />
          </div>

          <h2 className="text-xl font-bold mb-2 break-words">
            {product.name}
          </h2>

          <div className="text-2xl font-bold text-primary mb-4">
            {product.price.toLocaleString('ru-RU')} ₽
          </div>

          <div className="text-muted-foreground mb-5 break-words">
            {product.description || 'Описание отсутствует'}
          </div>

          <div className="text-xs text-muted-foreground mb-3 flex items-center gap-2">
            <ZoomIn className="h-4 w-4" />
            Двойное нажатие увеличивает фото
          </div>

          <div className="flex flex-col gap-3">
            {cartItem ? (
              <>
                <div className="flex items-center border border-border rounded-full overflow-hidden justify-center">
                  <button
                    className="bg-muted hover:bg-muted/80 w-10 h-10 flex items-center justify-center"
                    onClick={() => handleUpdateQuantity(cartItem.quantity - 1)}
                    onPointerDown={(e) => {
                      if (e.pointerType === 'touch') {
                        e.preventDefault();
                        handleUpdateQuantity(cartItem.quantity - 1);
                      }
                    }}
                  >
                    <Minus className="h-4 w-4" />
                  </button>
                  <span className="w-12 text-center font-medium">
                    {cartItem.quantity}
                  </span>
                  <button
                    className="bg-muted hover:bg-muted/80 w-10 h-10 flex items-center justify-center"
                    onClick={() => handleUpdateQuantity(cartItem.quantity + 1)}
                    onPointerDown={(e) => {
                      if (e.pointerType === 'touch') {
                        e.preventDefault();
                        handleUpdateQuantity(cartItem.quantity + 1);
                      }
                    }}
                  >
                    <Plus className="h-4 w-4" />
                  </button>
                </div>
                <Button
                  variant="outline"
                  onClick={handleRemoveClick}
                  className="gap-2"
                >
                  <Trash2 className="h-4 w-4" />
                  Удалить из корзины
                </Button>
              </>
            ) : (
              <Button onClick={handleAddToCart} className="gap-2">
                <ShoppingCart className="h-4 w-4" />
                Добавить в корзину
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {showZoom && (
        <div
          className="fixed inset-0 bg-black/95 flex items-center justify-center z-[100] p-5"
          onClick={() => setShowZoom(false)}
        >
          <button
            className="absolute top-5 right-5 text-white bg-black/50 rounded-full w-10 h-10 flex items-center justify-center hover:bg-black/70"
            onClick={() => setShowZoom(false)}
          >
            <X className="h-6 w-6" />
          </button>
          <img
            src={photoUrl}
            alt={product.name}
            className="max-w-full max-h-[80vh] object-contain rounded-lg"
            onError={(e) => {
              e.currentTarget.src = IMAGES.placeholder;
            }}
          />
        </div>
      )}

      <AlertDialog open={deleteConfirm} onOpenChange={setDeleteConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить товар из корзины?</AlertDialogTitle>
            <AlertDialogDescription>
              Вы уверены, что хотите удалить "{product.name}" из корзины? Это действие нельзя отменить.
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
    </>
  );
};
