import { Product, CartItem } from '@/types/shop.types';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ShoppingCart, Plus, Minus } from 'lucide-react';
import { IMAGES } from '@/config/app.config';

interface ProductCardProps {
  product: Product;
  cartItem: CartItem | undefined;
  onAddToCart: () => void;
  onUpdateQuantity: (newQuantity: number) => void;
  onProductClick: () => void;
}

export const ProductCard = ({
  product,
  cartItem,
  onAddToCart,
  onUpdateQuantity,
  onProductClick,
}: ProductCardProps) => {
  const resolvePhotoUrl = (photoUrl?: string) => {
    if (!photoUrl) return IMAGES.placeholder;
    if (photoUrl.startsWith('http://') || photoUrl.startsWith('https://')) {
      return photoUrl;
    }
    if (photoUrl.startsWith('/static/')) {
      return photoUrl;
    }
    return `/static/${photoUrl}`;
  };

  const photoUrl = resolvePhotoUrl(product.photo_url);

  return (
    <Card
      className="cursor-pointer transition-all hover:-translate-y-1 hover:shadow-lg overflow-hidden"
      onClick={onProductClick}
      onDoubleClick={(e) => {
        e.preventDefault();
        onProductClick();
      }}
    >
      <div className="relative w-full aspect-[3/4] overflow-hidden product-image-container active:scale-[0.99] transition bg-white">
        {/* Template.jpg как фон - не влияет на высоту */}
        <div className="absolute inset-0 product-image-container-bg" />
        
        {/* Изображение товара - определяет высоту контейнера */}
        <img
          src={photoUrl}
          alt={product.name}
          className="relative h-full w-full object-cover transition-transform"
          onError={(e) => {
            e.currentTarget.src = IMAGES.placeholder;
          }}
        />
      </div>
      
      <CardContent className="p-3">
        <div className="font-semibold text-sm mb-1 line-clamp-2 min-h-[2.5em]">
          {product.name}
        </div>
        
        <div className="text-primary font-bold text-base mb-2">
          {product.price.toLocaleString('ru-RU')} ₽
        </div>

        <div onClick={(e) => e.stopPropagation()}>
          {cartItem ? (
            <div className="flex items-center border border-border rounded-full overflow-hidden">
              <button
                className="bg-muted hover:bg-muted/80 active:scale-95 w-8 h-8 flex items-center justify-center font-semibold transition"
                onClick={() => onUpdateQuantity(cartItem.quantity - 1)}
              >
                <Minus className="h-4 w-4" />
              </button>
              <span className="flex-1 text-center font-medium">
                {cartItem.quantity}
              </span>
              <button
                className="bg-muted hover:bg-muted/80 active:scale-95 w-8 h-8 flex items-center justify-center font-semibold transition"
                onClick={() => onUpdateQuantity(cartItem.quantity + 1)}
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <Button
              className="w-full gap-2 active:scale-[0.98] transition"
              size="sm"
              onClick={onAddToCart}
            >
              <ShoppingCart className="h-4 w-4" />
              В корзину
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
