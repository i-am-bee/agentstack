/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useParams } from 'next/navigation';

export function useParamsFromUrl() {
  const { providerId, contextId } = useParams<{ providerId?: string; contextId?: string }>();

  return {
    providerId,
    contextId,
  };
}
