/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, ToastNotification } from '@carbon/react';
import clsx from 'clsx';
import { formatDistanceToNow } from 'date-fns';
import type { PropsWithChildren } from 'react';
import { useCallback, useEffect, useMemo, useState } from 'react';
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
          date: new Date(),
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

function Toast({ toast, onClose }: { toast: ToastWithKey; onClose: () => void }) {
  const { key, icon: Icon, date, title, subtitle, apiError, inlineIcon, hideTimeElapsed, ...otherProps } = toast;

  return (
    <ToastNotification
      key={key}
      {...otherProps}
      onClose={onClose}
      className={clsx({
        'cds--toast-notification--custom-icon': Boolean(Icon),
        'cds--toast-notification--inline-icon': Boolean(inlineIcon),
      })}
    >
      {Icon && <Icon className="cds--toast-notification__icon" />}

      <div className="cds--toast-notification__caption">{!hideTimeElapsed && date && <ElapsedTime date={date} />}</div>

      {title && <div className="cds--toast-notification__title">{title}</div>}

      {(subtitle || apiError) && (
        <div className="cds--toast-notification__subtitle">
          {subtitle && <div className={classes.subtitle}>{subtitle}</div>}
          {apiError && <div className={classes.apiError}>{apiError}</div>}
        </div>
      )}
    </ToastNotification>
  );
}

function ElapsedTime({ date }: { date: Date }) {
  const [, setTick] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setTick((tick) => tick + 1);
    }, TIME_REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  if (Date.now() - date.getTime() < 5_000) {
    return 'Just now';
  }

  return formatDistanceToNow(date, { addSuffix: true, includeSeconds: true });
}

const TIME_REFRESH_INTERVAL = 10_000; // 10 seconds
