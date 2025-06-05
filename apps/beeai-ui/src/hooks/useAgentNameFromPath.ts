/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { usePathname } from 'next/navigation';

export function useAgentNameFromPath() {
  const pathname = usePathname();
  const parts = pathname?.split('/');

  if (parts?.at(1) === 'agents') {
    return parts.at(2);
  }

  return null;
}
