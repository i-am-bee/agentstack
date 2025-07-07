/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useCallback } from 'react';

export function useUpdateSearchParams() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const updateSearchParams = useCallback(
    (params: Record<string, string | number | boolean>) => {
      const newSearchParams = new URLSearchParams(searchParams ?? undefined);
      Object.entries(params).forEach(([key, value]) => {
        if (value) {
          newSearchParams.set(key, String(value));
        } else {
          newSearchParams.delete(key);
        }
      });
      router.push(`${pathname}?${newSearchParams.toString()}`);
    },
    [pathname, router, searchParams],
  );

  return { updateSearchParams };
}
