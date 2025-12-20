
import { LucideIcon, Package } from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  message: string;
}

export const EmptyState = ({ icon: Icon = Package, message }: EmptyStateProps) => {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
      <Icon className="h-16 w-16 mb-4 opacity-30" />
      <p>{message}</p>
    </div>
  );
};
