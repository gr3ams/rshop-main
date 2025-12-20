
import { useState } from 'react';
import { Search, Filter, X, ChevronDown, ChevronUp } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Category, Brand } from '@/types/shop.types';
import { cn } from '@/lib/utils';

interface SearchFilterProps {
  categories: Category[];
  brands: Brand[];
  onFilter: (filters: {
    categoryId: number | null;
    brandId: number | null;
    searchText: string;
    minPrice: number | null;
    maxPrice: number | null;
  }) => void;
}

export const SearchFilter = ({ categories, brands, onFilter }: SearchFilterProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedBrand, setSelectedBrand] = useState<string>('');
  const [searchText, setSearchText] = useState('');
  const [minPrice, setMinPrice] = useState<string>('');
  const [maxPrice, setMaxPrice] = useState<string>('');

  // Для фильтрации брендов по категории используем все бренды, если категория не выбрана
  // Если выбрана категория, показываем бренды, которые есть в этой категории (через продукты)
  const filteredBrands = brands;

  const handleApply = () => {
    onFilter({
      categoryId: selectedCategory && selectedCategory !== 'all' ? Number(selectedCategory) : null,
      brandId: selectedBrand && selectedBrand !== 'all' ? Number(selectedBrand) : null,
      searchText: searchText.trim(),
      minPrice: minPrice ? Number(minPrice) : null,
      maxPrice: maxPrice ? Number(maxPrice) : null,
    });
    setIsOpen(false);
  };

  const handleReset = () => {
    setSelectedCategory('');
    setSelectedBrand('');
    setSearchText('');
    setMinPrice('');
    setMaxPrice('');
    onFilter({
      categoryId: null,
      brandId: null,
      searchText: '',
      minPrice: null,
      maxPrice: null,
    });
    setIsOpen(false);
  };

  const hasActiveFilters = selectedCategory || selectedBrand || searchText || minPrice || maxPrice;

  return (
    <div className="mb-4">
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Поиск по названию..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleApply();
              }
            }}
            className="pl-10"
          />
        </div>
        <Button
          variant={hasActiveFilters ? "default" : "outline"}
          size="icon"
          onClick={() => setIsOpen(!isOpen)}
          className={cn(
            "relative",
            hasActiveFilters && "bg-primary text-primary-foreground"
          )}
        >
          <Filter className="h-4 w-4" />
          {hasActiveFilters && (
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-destructive rounded-full border-2 border-background" />
          )}
        </Button>
      </div>

      {isOpen && (
        <Card className="mt-3 border-border/50">
          <CardContent className="p-4 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Фильтры</h3>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Категория</Label>
                <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                  <SelectTrigger>
                    <SelectValue placeholder="Все категории" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Все категории</SelectItem>
                    {categories.map((cat) => (
                      <SelectItem key={cat.id} value={cat.id.toString()}>
                        {cat.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Бренд</Label>
                <Select
                  value={selectedBrand}
                  onValueChange={setSelectedBrand}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Все бренды" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Все бренды</SelectItem>
                    {filteredBrands.map((brand) => (
                      <SelectItem key={brand.id} value={brand.id.toString()}>
                        {brand.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Цена, ₽</Label>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <Label htmlFor="minPrice" className="text-xs text-muted-foreground">
                      От
                    </Label>
                    <Input
                      id="minPrice"
                      type="number"
                      placeholder="0"
                      value={minPrice}
                      onChange={(e) => setMinPrice(e.target.value)}
                      min="0"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="maxPrice" className="text-xs text-muted-foreground">
                      До
                    </Label>
                    <Input
                      id="maxPrice"
                      type="number"
                      placeholder="∞"
                      value={maxPrice}
                      onChange={(e) => setMaxPrice(e.target.value)}
                      min={minPrice || "0"}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-2 pt-2 border-t">
              <Button
                variant="outline"
                onClick={handleReset}
                className="flex-1"
              >
                Сбросить
              </Button>
              <Button
                onClick={handleApply}
                className="flex-1"
              >
                Применить
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
