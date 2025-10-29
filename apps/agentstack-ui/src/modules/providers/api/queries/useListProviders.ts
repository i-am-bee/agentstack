/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { listProviders } from '..';
import { providerKeys } from '../keys';
import type { ListProvidersParams } from '../types';

interface Props extends ListProvidersParams {
  enabled?: boolean;
}

export function useListProviders({ enabled = true, ...params }: Props = {}) {
  const query = useQuery({
    queryKey: providerKeys.list(params),
    queryFn: () => listProviders(params),
    enabled,
  });

  return query;
}
