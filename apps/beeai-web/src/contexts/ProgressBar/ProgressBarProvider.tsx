/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { ProgressProvider } from '@bprogress/next/app';
import { PropsWithChildren } from 'react';

export function ProgressBarProvider({ children }: PropsWithChildren) {
  return (
    <ProgressProvider color="#0f62fe" height="3px" options={{ showSpinner: false }} shallowRouting>
      {children}
    </ProgressProvider>
  );
}
