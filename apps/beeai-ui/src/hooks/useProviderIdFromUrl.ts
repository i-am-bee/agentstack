/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useSearchParams } from 'next/navigation';

export function useProviderIdFromUrl() {
  const searchParams = useSearchParams();
  const providerId = searchParams.get('p');

  return providerId ? decodeURIComponent(providerId) : null;
}
