/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from '@carbon/react';
import type { PropsWithChildren } from 'react';
import { useCallback, useMemo, useState } from 'react';
import { v4 as uuid } from 'uuid';

import { Toast } from '#components/Toast/Toast.tsx';
import { useScrollbar } from '#hooks/useScrollbar.ts';

import type { Toast as ToastProps, ToastWithKey } from './toast-context';
import { ToastContext } from './toast-context';
import classes from './ToastProvider.module.scss';

export function ToastProvider({ children }: PropsWithChildren) {
  const [toasts, setToasts] = useState<ToastWithKey[]>([]);

  const { ref: scrollbarRef, ...scrollbarProps } = useScrollbar();

  const addToast = useCallback(
    (toast: ToastProps) => {
      setToasts((existing) => {
        const defaults = {
          key: uuid(),
          date: new Date(),
          timeout: 10_000,
        };
        return [{ ...defaults, ...toast }, ...existing];
      });
    },
    [setToasts],
  );

  const contextValue = useMemo(() => ({ addToast }), [addToast]);
  return (
    <ToastContext.Provider value={contextValue}>
      {children}

      <div className={classes.toasts} ref={scrollbarRef} {...scrollbarProps}>
        {toasts.length > 1 && (
          <div className={classes.clearButton}>
            <Button kind="ghost" size="sm" onClick={() => setToasts([])}>
              Clear all
            </Button>
          </div>
        )}

        {toasts.map((toast) => (
          <Toast
            key={toast.key}
            toast={toast}
            onClose={() => {
              setToasts((existing) => existing.filter(({ key }) => key !== toast.key));
            }}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
}
