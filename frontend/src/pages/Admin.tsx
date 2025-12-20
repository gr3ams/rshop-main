
import { useTelegramWebApp } from '@/hooks/useTelegramWebApp';
import { AdminProductForm } from '@/components/admin/AdminProductForm';
import { LoadingSpinner } from '@/components/shop/LoadingSpinner';
import { isAdmin } from '@/config/app.config';

export const Admin = () => {
  const { isReady, user } = useTelegramWebApp();

  if (!isReady) {
    return <LoadingSpinner />;
  }

  // Проверка прав администратора
  if (!isAdmin(user?.id)) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-2">Доступ запрещен</h1>
          <p className="text-muted-foreground">У вас нет прав для доступа к этой странице</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 bg-background">
      <div className="max-w-4xl mx-auto">
        <AdminProductForm />
      </div>
    </div>
  );
};
