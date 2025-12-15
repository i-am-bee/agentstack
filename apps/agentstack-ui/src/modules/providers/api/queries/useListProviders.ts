/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';
import type { ListProvidersRequest } from 'agentstack-sdk';

import { listProviders } from '..';
import { providerKeys } from '../keys';

interface Props extends ListProvidersRequest {
  enabled?: boolean;
}

export function useListProviders({ enabled = true, ...request }: Props = {}) {
  const query = useQuery({
    queryKey: providerKeys.list(request),
    queryFn: () => listProviders(request),
    enabled,
  });

  return query;
}
