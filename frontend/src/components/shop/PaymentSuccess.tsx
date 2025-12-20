
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { CheckCircle, Check } from 'lucide-react';

interface PaymentSuccessProps {
  onBackToShop: () => void;
}

export const PaymentSuccess = ({ onBackToShop }: PaymentSuccessProps) => {
  return (
    <div className="flex flex-col items-center justify-center py-10">
      <Card className="max-w-md w-full">
        <CardContent className="flex flex-col items-center py-12 px-6">
          <CheckCircle className="h-24 w-24 text-green-500 mb-6" />
          <h3 className="text-2xl font-bold mb-3">Ваш заказ оформлен!</h3>
          <p className="text-muted-foreground text-center mb-8">
            Мы свяжемся с вами для подтверждения
          </p>
          <Button onClick={onBackToShop} className="gap-2">
            <Check className="h-4 w-4" />
            Вернуться в магазин
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};
