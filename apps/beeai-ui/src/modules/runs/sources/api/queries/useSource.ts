/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { sourceKeys } from '../keys';
import type { SourceMetadata, SourceReference } from '../types';

interface Params {
  source: SourceReference;
}

export function useSource({ source }: Params) {
  const query = useQuery({
    queryKey: sourceKeys.detail({ source }),
    queryFn: async () => {
      return {
        ...source,
        metadata: {
          title: source.title ?? source.url,
          description: source.description,
        } as SourceMetadata,
      };
    },
  });

  return query;
}
