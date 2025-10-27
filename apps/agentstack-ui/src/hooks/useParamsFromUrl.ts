/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { usePathname } from 'next/navigation';

export function useParamsFromUrl() {
  const pathname = usePathname();

  // Parse parameters from pathname: /run/[providerId]/c/[contextId] or /run/[providerId]
  // because useParams does not react to changes in the URL via history.pushState
  const match = pathname.match(/^\/run\/([^/]+)(?:\/c\/([^/]+))?/);

  const providerId = match?.at(1);
  const contextId = match?.at(2);

  return {
    providerId,
    contextId,
  };
}
