
import { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'dark' | 'light' | 'system';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Функция для получения начальной темы из Telegram WebApp
const getInitialTheme = (): Theme => {
  // Проверяем Telegram WebApp данные
  if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
    const tg = window.Telegram.WebApp;
    
    // Telegram WebApp имеет colorScheme напрямую
    // Также проверяем themeParams.colorScheme
    const colorScheme = (tg as any).colorScheme || (tg as any).themeParams?.colorScheme;
    
    if (colorScheme === 'dark') {
      return 'dark';
    } else if (colorScheme === 'light') {
      return 'light';
    }
    
    // Альтернативный способ: проверяем через themeParams
    const themeParams = (tg as any).themeParams;
    if (themeParams?.bg_color) {
      // Если фон темный, вероятно тема dark
      const bgColor = themeParams.bg_color;
      // Простая проверка: если цвет темный (меньше определенного порога)
      const rgb = parseInt(bgColor.replace('#', ''), 16);
      const r = (rgb >> 16) & 0xff;
      const g = (rgb >> 8) & 0xff;
      const b = rgb & 0xff;
      const brightness = (r * 299 + g * 587 + b * 114) / 1000;
      if (brightness < 128) {
        return 'dark';
      }
    }
  }
  
  // Fallback: проверяем localStorage
  const savedTheme = localStorage.getItem('theme') as Theme | null;
  if (savedTheme && ['dark', 'light', 'system'].includes(savedTheme)) {
    return savedTheme;
  }
  
  // Fallback: системная тема
  return 'system';
};

export const ThemeProvider = ({ children }: { children: React.ReactNode }) => {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');

    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }
    
    // Сохраняем выбор темы в localStorage
    localStorage.setItem('theme', theme);
  }, [theme]);
  
  // Слушаем изменения темы Telegram WebApp
  useEffect(() => {
    if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
      const tg = window.Telegram.WebApp;
      
      // Слушаем изменения colorScheme
      const handleColorSchemeChange = () => {
        const colorScheme = (tg as any).colorScheme;
        if (colorScheme === 'dark' || colorScheme === 'light') {
          setTheme(colorScheme);
        }
      };
      
      // Проверяем наличие метода onEvent
      if ((tg as any).onEvent) {
        (tg as any).onEvent('themeChanged', handleColorSchemeChange);
      }
      
      return () => {
        if ((tg as any).offEvent) {
          (tg as any).offEvent('themeChanged', handleColorSchemeChange);
        }
      };
    }
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
};
