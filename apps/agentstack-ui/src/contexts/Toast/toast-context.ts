/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import type { IconProps } from '@carbon/icons-react/lib/Icon';
import type { ComponentType } from 'react';
import { createContext } from 'react';

export interface Toast {
  title: string;
  kind?: 'info' | 'error';
  timeout?: number;
  icon?: ComponentType<IconProps>;
  date?: Date;
  message?: string;
  hideDate?: boolean;
  renderMarkdown?: true;
}

export interface ToastContextValue {
  addToast: (toast: Toast) => void;
}

export const ToastContext = createContext<ToastContextValue>(null as unknown as ToastContextValue);

export interface ToastWithKey extends Toast {
  key: string;
}
