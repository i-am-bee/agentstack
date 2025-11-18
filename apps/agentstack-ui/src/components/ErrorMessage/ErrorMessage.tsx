/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ActionableNotification, Button, InlineLoading } from '@carbon/react';
import type { ReactNode } from 'react';

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';

import classes from './ErrorMessage.module.scss';

interface Props {
  title?: string;
  subtitle?: string;
  onRetry?: () => void;
  isRefetching?: boolean;
  children?: ReactNode;
}

export function ErrorMessage({ title, subtitle, onRetry, isRefetching, children }: Props) {
  return (
    <ActionableNotification title={title} kind="error" lowContrast hideCloseButton>
      {(subtitle || onRetry) && (
        <div className={classes.body}>
          {subtitle && <MarkdownContent>{subtitle}</MarkdownContent>}

          {onRetry && (
            <Button size="sm" onClick={() => onRetry()} disabled={isRefetching}>
              {!isRefetching ? 'Retry' : <InlineLoading description="Retrying&hellip;" />}
            </Button>
          )}
          {children}
        </div>
      )}
    </ActionableNotification>
  );
}
