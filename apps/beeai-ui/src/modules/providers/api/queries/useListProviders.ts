/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { listProviders } from '..';
import { providerKeys } from '../keys';

export function useListProviders() {
  const query = useQuery({
    queryKey: providerKeys.list(),
    queryFn: listProviders,
  });

  return query;
}
