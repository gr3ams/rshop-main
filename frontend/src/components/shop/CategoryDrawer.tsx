import { Category } from "@/types/shop.types";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Filter, Sparkles, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useState } from "react";

interface CategoryDrawerProps {
  categories: Category[];
  activeCategoryId: number | null;
  onSelectCategory: (categoryId: number | null) => void;
}

export const CategoryDrawer = ({
  categories,
  activeCategoryId,
  onSelectCategory,
}: CategoryDrawerProps) => {
  const [open, setOpen] = useState(false);

  const handleSelect = (id: number | null) => {
    onSelectCategory(id);
    setOpen(false);
  };

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant={activeCategoryId ? "default" : "outline"}
          size="sm"
          className="rounded-full gap-2 shadow-md active:scale-95 transition"
        >
          <Filter className="h-4 w-4" />
          Категории
          {activeCategoryId && (
            <span className="text-xs bg-primary-foreground/20 px-2 py-0.5 rounded-full">
              выбрана
            </span>
          )}
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-[85vw] max-w-sm p-4">
        <SheetHeader className="flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <SheetTitle>Категории</SheetTitle>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => handleSelect(null)}
            className="rounded-full"
          >
            <X className="h-4 w-4" />
          </Button>
        </SheetHeader>

        <div className="mt-4 space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => handleSelect(null)}
              className={cn(
                "p-3 rounded-xl border text-left transition shadow-sm active:scale-[0.98]",
                activeCategoryId === null
                  ? "bg-primary text-primary-foreground border-primary"
                  : "bg-card hover:bg-primary/5"
              )}
            >
              Все товары
            </button>
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => handleSelect(category.id)}
                className={cn(
                  "p-3 rounded-xl border text-left transition shadow-sm active:scale-[0.98]",
                  activeCategoryId === category.id
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-card hover:bg-primary/5"
                )}
              >
                {category.name}
              </button>
            ))}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};
