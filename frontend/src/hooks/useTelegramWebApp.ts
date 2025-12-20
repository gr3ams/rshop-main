
import { useEffect, useState } from 'react';
import { getCurrentModeConfig } from '@/config/app.config';

interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
}

interface TelegramWebApp {
  initData: string;
  initDataUnsafe: {
    user?: TelegramUser;
  };
  expand: () => void;
  close: () => void;
  setHeaderColor: (color: string) => void;
  setBackgroundColor: (color: string) => void;
  showAlert: (message: string) => void;
  openTelegramLink?: (url: string) => void;
  openLink?: (url: string) => void;
}

declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp;
    };
  }
}

export const useTelegramWebApp = () => {
  const [isReady, setIsReady] = useState(false);
  const [user, setUser] = useState<TelegramUser | null>(null);
  const config = getCurrentModeConfig();

  useEffect(() => {
    if (config.checkTelegram && window.Telegram?.WebApp) {
      const tg = window.Telegram.WebApp;
      
      // Настройка внешнего вида
      tg.expand();
      tg.setHeaderColor('#4361ee');
      tg.setBackgroundColor('#f8f9fa');
      
      // Получение пользователя
      if (tg.initDataUnsafe.user) {
        setUser(tg.initDataUnsafe.user);
      }
      
      setIsReady(true);
    } else if (!config.checkTelegram) {
      // В режиме отладки без Telegram
      setIsReady(true);
      setUser(null);
    }
  }, [config.checkTelegram]);

  const showAlert = (message: string) => {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.showAlert(message);
    } else {
      alert(message);
    }
  };

  const close = () => {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.close();
    }
  };

  return {
    isReady,
    user,
    showAlert,
    close,
    requireTelegram: config.requireTelegram,
  };
};
