/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { readConfig } from '.';

export function useReadConfig() {
  const query = useQuery({
    queryKey: ['config'],
    queryFn: readConfig,
    staleTime: Infinity,
  });

  return query;
}
