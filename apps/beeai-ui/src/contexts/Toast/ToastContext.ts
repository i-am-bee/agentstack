import { createContext, ReactNode } from 'react';

export interface Toast {
  /**
   * Provide a description for "close" icon button that can be read by screen readers
   */
  ariaLabel?: string;
  caption?: string;
  children?: ReactNode;
  hideCloseButton?: boolean;
  kind?: 'error' | 'info' | 'info-square' | 'success' | 'warning' | 'warning-alt';
  lowContrast?: boolean;
  role?: 'alert' | 'log' | 'status';
  /** Provide a description for "status" icon that can be read by screen readers */
  statusIconDescription?: string;
  subtitle?: string;
  /** Specify an optional duration the notification should be closed in */
  timeout?: number;
  title?: string;
  apiError?: string;
}

export interface ToastContextValue {
  addToast: (toast: Toast) => void;
}

export const ToastContext = createContext<ToastContextValue>(null as unknown as ToastContextValue);

export interface ToastWithKey extends Toast {
  key: string;
}
