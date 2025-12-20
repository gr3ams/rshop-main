
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { ThemeProvider } from "./components/ThemeProvider";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Shop } from "./pages/Shop";
import { Admin } from "./pages/Admin";
import { Payment } from "./pages/Payment";
import NotFound from "./pages/NotFound";
import { PENDING_ORDER_KEY } from "./components/shop/CheckoutForm";

const queryClient = new QueryClient();

// Компонент для проверки pending_order при загрузке
const PendingOrderCheck = () => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Проверяем наличие pending_order только если не находимся уже на странице оплаты
    if (location.pathname !== '/payment') {
      const pendingOrder = localStorage.getItem(PENDING_ORDER_KEY);
      if (pendingOrder) {
        // Перенаправляем на страницу оплаты
        navigate('/payment', { replace: true });
      }
    }
  }, [location.pathname, navigate]);

  return null;
};

const App = () => (
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <TooltipProvider>
          <Sonner />
          <BrowserRouter>
            <PendingOrderCheck />
            <Routes>
              <Route path="/" element={<Shop />} />
              <Route path="/admin" element={<Admin />} />
              <Route path="/payment" element={<Payment />} />
              {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  </ErrorBoundary>
);

export default App;
