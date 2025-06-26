/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, ToastNotification } from '@carbon/react';
import clsx from 'clsx';
import type { PropsWithChildren } from 'react';
import { useCallback, useMemo, useState } from 'react';
import { v4 as uuid } from 'uuid';

import type { Toast, ToastWithKey } from './toast-context';
import { ToastContext } from './toast-context';
import classes from './ToastProvider.module.scss';

export function ToastProvider({ children }: PropsWithChildren) {
  const [toasts, setToasts] = useState<ToastWithKey[]>([]);

  const addToast = useCallback(
    (toast: Toast) => {
      setToasts((existing) => {
        const defaults = {
          lowContrast: true,
          timeout: 10000,
          key: uuid(),
          caption: new Date().toLocaleString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          }),
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

      <div className={classes.toasts}>
        {toasts.length > 1 && (
          <div className={classes.clearButton}>
            <Button kind="ghost" size="sm" onClick={() => setToasts([])}>
              Clear all
            </Button>
          </div>
        )}

        {toasts.map(({ key, icon: Icon, caption, title, subtitle, apiError, ...toast }) => (
          <ToastNotification
            key={key}
            {...toast}
            onClose={() => {
              setToasts((existing) => existing.filter((toast) => toast.key !== key));
            }}
            className={clsx({ 'cds--toast-notification--custom-icon': Icon })}
          >
            {Icon && <Icon className="cds--toast-notification__icon" />}

            {caption && <div className="cds--toast-notification__caption">{caption}</div>}

            {title && <div className="cds--toast-notification__title">{title}</div>}

            {(subtitle || apiError) && (
              <div className="cds--toast-notification__subtitle">
                {subtitle && <div className={classes.subtitle}>{subtitle}</div>}
                {apiError && <div className={classes.apiError}>{apiError}</div>}
              </div>
            )}
          </ToastNotification>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
