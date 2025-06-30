/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FallbackProps } from 'react-error-boundary';

import { ErrorLayout } from '../layouts/ErrorLayout';

export function ErrorFallback({ error }: FallbackProps) {
  return (
    <ErrorLayout>
      <h1>Something went wrong</h1>

      <p>{error.message}</p>
    </ErrorLayout>
  );
}
