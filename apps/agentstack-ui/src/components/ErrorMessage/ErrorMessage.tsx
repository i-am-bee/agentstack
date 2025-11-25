/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ActionableNotification, Button, InlineLoading } from '@carbon/react';
import type { ReactNode } from 'react';

import { NotificationMarkdownContent } from '#components/NotificationMarkdownContent/NotificationMarkdownContent.tsx';

import classes from './ErrorMessage.module.scss';

interface Props {
  title?: string;
  message?: string;
  onRetry?: () => void;
  isRefetching?: boolean;
  children?: ReactNode;
}

export function ErrorMessage({ title, message, onRetry, isRefetching }: Props) {
  return (
    <ActionableNotification title={title} kind="error" lowContrast hideCloseButton>
      {(message || onRetry) && (
        <div className={classes.body}>
          {message && <NotificationMarkdownContent>{message}</NotificationMarkdownContent>}

          {onRetry && (
            <Button size="sm" onClick={() => onRetry()} disabled={isRefetching}>
              {!isRefetching ? 'Retry' : <InlineLoading description="Retrying&hellip;" />}
            </Button>
          )}
        </div>
      )}
    </ActionableNotification>
  );
}
