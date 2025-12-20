
import { useState, useEffect } from 'react';
import { useTelegramWebApp } from '@/hooks/useTelegramWebApp';
import { api } from '@/lib/api';
import { Brand, Category } from '@/types/shop.types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/shop/LoadingSpinner';
import { ErrorMessage } from '@/components/shop/ErrorMessage';
import { toast } from 'sonner';

export const AdminProductForm = () => {
  const { showAlert, close } = useTelegramWebApp();
  const [categories, setCategories] = useState<Category[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    categoryId: '',
    brandId: '',
    name: '',
    price: '',
    photo: null as File | null,
    description: '',
  });

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAdminData();
      setCategories(data.categories);
    } catch (error) {
      setError('Не удалось загрузить данные');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const loadBrands = async (categoryId: string) => {
    if (!categoryId) return;
    try {
      const data = await api.getBrands(Number(categoryId));
      setBrands(data);
    } catch (error) {
      toast.error('Не удалось загрузить бренды');
      console.error(error);
    }
  };

  const handleCategoryChange = (categoryId: string) => {
    setFormData({ ...formData, categoryId, brandId: '' });
    loadBrands(categoryId);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.photo) {
      toast.error('Пожалуйста, выберите фото');
      return;
    }

    setSubmitting(true);
    
    const submitData = new FormData();
    submitData.append('category_id', formData.categoryId);
    submitData.append('brand_id', formData.brandId);
    submitData.append('name', formData.name);
    submitData.append('price', formData.price);
    submitData.append('photo', formData.photo);
    submitData.append('description', formData.description);

    try {
      await api.addProduct(submitData);
      showAlert('Товар успешно добавлен!');
      close();
    } catch (error) {
      toast.error('Ошибка при добавлении товара');
      console.error(error);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={loadCategories} />;
  }

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Добавление товара</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="category">Категория</Label>
            <Select
              value={formData.categoryId}
              onValueChange={handleCategoryChange}
              required
            >
              <SelectTrigger id="category">
                <SelectValue placeholder="Выберите категорию" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((category) => (
                  <SelectItem key={category.id} value={String(category.id)}>
                    {category.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="brand">Бренд</Label>
            <Select
              value={formData.brandId}
              onValueChange={(value) => setFormData({ ...formData, brandId: value })}
              disabled={!formData.categoryId}
              required
            >
              <SelectTrigger id="brand">
                <SelectValue placeholder="Выберите бренд" />
              </SelectTrigger>
              <SelectContent>
                {brands.map((brand) => (
                  <SelectItem key={brand.id} value={String(brand.id)}>
                    {brand.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="name">Название</Label>
            <Input
              id="name"
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="price">Цена</Label>
            <Input
              id="price"
              type="number"
              required
              value={formData.price}
              onChange={(e) => setFormData({ ...formData, price: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="photo">Фото</Label>
            <Input
              id="photo"
              type="file"
              accept="image/*"
              required
              onChange={(e) =>
                setFormData({ ...formData, photo: e.target.files?.[0] || null })
              }
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Описание</Label>
            <Textarea
              id="description"
              rows={4}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>

          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? 'Добавление...' : 'Добавить'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};
