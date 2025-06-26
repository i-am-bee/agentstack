/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { listProviders } from '..';
import { providerKeys } from '../keys';

interface Props {
  source?: string;
}

export function useProviderBySource({ source }: Props) {
  const query = useQuery({
    queryKey: providerKeys.list(),
    queryFn: listProviders,
    select: (data) => data?.items.find((item) => source && source === item.source),
    enabled: Boolean(source),
  });

  return query;
}
