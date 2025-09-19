/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useSearchParams } from 'next/navigation';

export function useParamsFromUrl() {
  const searchParams = useSearchParams();
  const providerId = searchParams.get('p');
  const contextId = searchParams.get('c');

  return {
    providerId: providerId ? decodeURIComponent(providerId) : null,
    contextId: contextId ? decodeURIComponent(contextId) : null,
  };
}
