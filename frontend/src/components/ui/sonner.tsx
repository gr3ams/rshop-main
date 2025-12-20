
import { useTheme } from "@/components/ThemeProvider";
import { Toaster as Sonner, toast as sonnerToast } from "sonner";
import * as React from "react";

type ToasterProps = React.ComponentProps<typeof Sonner>;

// Константа для ID уведомлений - используем один ID для всех, чтобы старое автоматически заменялось новым
const MAIN_TOAST_ID = 'main-toast';

// Обертка для toast, которая автоматически заменяет предыдущее уведомление
const toast = {
  success: (message: string, options?: Parameters<typeof sonnerToast.success>[1]) => {
    // Используем один ID - Sonner автоматически заменит старое уведомление новым
    return sonnerToast.success(message, {
      ...options,
      id: MAIN_TOAST_ID,
    });
  },
  error: (message: string, options?: Parameters<typeof sonnerToast.error>[1]) => {
    return sonnerToast.error(message, {
      ...options,
      id: MAIN_TOAST_ID,
    });
  },
  info: (message: string, options?: Parameters<typeof sonnerToast.info>[1]) => {
    return sonnerToast.info(message, {
      ...options,
      id: MAIN_TOAST_ID,
    });
  },
  warning: (message: string, options?: Parameters<typeof sonnerToast.warning>[1]) => {
    return sonnerToast.warning(message, {
      ...options,
      id: MAIN_TOAST_ID,
    });
  },
  dismiss: (toastId?: string | number) => {
    sonnerToast.dismiss(toastId);
  },
  // Экспортируем остальные методы напрямую
  promise: sonnerToast.promise,
  loading: sonnerToast.loading,
  custom: sonnerToast.custom,
};

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme } = useTheme();
  
  // Определяем актуальную тему (учитываем system)
  const actualTheme = React.useMemo((): 'light' | 'dark' => {
    if (theme === 'system') {
      const root = window.document.documentElement;
      return root.classList.contains('dark') ? 'dark' : 'light';
    }
    return theme;
  }, [theme]);

  return (
    <Sonner
      theme={actualTheme}
      className="toaster group"
      position="top-center"
      offset="0px"
      gap={8}
      closeButton
      duration={3000}
      expand={false}
      visibleToasts={1}
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-background/98 group-[.toaster]:text-foreground group-[.toaster]:border group-[.toaster]:border-border/50 group-[.toaster]:shadow-lg group-[.toaster]:rounded-lg group-[.toaster]:backdrop-blur-md group-[.toaster]:font-medium",
          description: "group-[.toast]:text-muted-foreground group-[.toast]:text-sm group-[.toast]:mt-1",
          actionButton: 
            "group-[.toast]:bg-primary group-[.toast]:text-primary-foreground group-[.toast]:hover:bg-primary/90 group-[.toast]:font-medium group-[.toast]:rounded-md",
          cancelButton: 
            "group-[.toast]:bg-muted group-[.toast]:text-muted-foreground group-[.toast]:hover:bg-muted/80 group-[.toast]:font-medium group-[.toast]:rounded-md",
          // Используем цвета темы вместо специфичных цветов
          success: "group-[.toaster]:bg-background/98 group-[.toaster]:text-foreground group-[.toaster]:border-border/50",
          error: "group-[.toaster]:bg-background/98 group-[.toaster]:text-foreground group-[.toaster]:border-border/50",
          info: "group-[.toaster]:bg-background/98 group-[.toaster]:text-foreground group-[.toaster]:border-border/50",
          warning: "group-[.toaster]:bg-background/98 group-[.toaster]:text-foreground group-[.toaster]:border-border/50",
        },
        style: {
          marginTop: "0",
        },
      }}
      {...props}
    />
  );
};

export { Toaster, toast };
