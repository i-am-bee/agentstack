/**
 * Copyright 2025 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { ActionableNotification, Button, InlineLoading } from '@carbon/react';
import { ReactNode } from 'react';
import classes from './ErrorMessage.module.scss';

interface Props {
  title: string;
  subtitle?: string;
  onRetry?: () => void;
  isRefetching?: boolean;
  children?: ReactNode;
}

export function ErrorMessage({ title, subtitle, onRetry, isRefetching, children }: Props) {
  return (
    <ActionableNotification className={classes.root} title={title} kind="error" lowContrast hideCloseButton>
      <div className={classes.body}>
        {subtitle && <p>{subtitle}</p>}
        {onRetry && (
          <Button size="md" onClick={() => onRetry()} disabled={isRefetching}>
            {!isRefetching ? 'Retry' : <InlineLoading description="Retrying..." />}
          </Button>
        )}
        {children}
      </div>
    </ActionableNotification>
  );
}
