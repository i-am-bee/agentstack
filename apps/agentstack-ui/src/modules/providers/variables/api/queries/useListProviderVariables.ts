/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { listProviderVariables } from '..';
import { providerVariableKeys } from '../keys';

interface Props {
  providerId?: string;
}

export function useListProviderVariables({ providerId = '' }: Props) {
  return useQuery({
    queryKey: providerVariableKeys.list(providerId),
    queryFn: () => listProviderVariables({ id: providerId }),
    enabled: Boolean(providerId),
  });
}
