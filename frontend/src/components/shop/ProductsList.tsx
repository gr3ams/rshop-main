
import { Product } from '@/types/shop.types';
import { useCart } from '@/hooks/useCart';
import { ProductCard } from './ProductCard';
import { ProductModal } from './ProductModal';
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
import { useState } from 'react';
import { PackageOpen } from 'lucide-react';
import { EmptyState } from './EmptyState';
import { IMAGES } from '@/config/app.config';
import { toast } from 'sonner';

interface ProductsListProps {
  products: Product[];
  categoryName: string;
}

export const ProductsList = ({ products, categoryName }: ProductsListProps) => {
  const { addToCart, updateCartItem, removeFromCart, getCartItem } = useCart();
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<{ open: boolean; productId: number | null; productName: string }>({
    open: false,
    productId: null,
    productName: '',
  });

  if (products.length === 0) {
    return <EmptyState icon={PackageOpen} message="Товаров в этой категории пока нет" />;
  }

  const handleAddToCart = (product: Product) => {
    const photoUrl = product.photo_url
      ? `/static/${product.photo_url}`
      : IMAGES.placeholder;

    addToCart({
      id: product.id,
      name: product.name,
      price: product.price,
      image: photoUrl,
      description: product.description,
    });
    
    toast.success(`${product.name} добавлен в корзину`);
  };

  const handleUpdateQuantity = (productId: number, productName: string, newQuantity: number) => {
    if (newQuantity <= 0) {
      // Показываем подтверждение при попытке удалить через уменьшение количества
      setDeleteConfirm({ open: true, productId, productName });
    } else {
      updateCartItem(productId, newQuantity);
      toast.success(`Количество "${productName}" изменено на ${newQuantity}`);
    }
  };

  const handleConfirmRemove = () => {
    if (deleteConfirm.productId !== null) {
      removeFromCart(deleteConfirm.productId);
      toast.success(`${deleteConfirm.productName} удален из корзины`);
      setDeleteConfirm({ open: false, productId: null, productName: '' });
    }
  };

  return (
    <>
      <h2 className="text-lg font-semibold mb-4">{categoryName}</h2>
      <div className="grid grid-cols-[repeat(auto-fill,minmax(160px,1fr))] gap-4">
        {products.map((product) => {
          const cartItem = getCartItem(product.id);
          
          return (
            <ProductCard
              key={product.id}
              product={product}
              cartItem={cartItem}
              onAddToCart={() => handleAddToCart(product)}
              onUpdateQuantity={(newQuantity) =>
                handleUpdateQuantity(product.id, product.name, newQuantity)
              }
              onProductClick={() => setSelectedProduct(product)}
            />
          );
        })}
      </div>

      {selectedProduct && (
        <ProductModal
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
        />
      )}

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
    </>
  );
};
