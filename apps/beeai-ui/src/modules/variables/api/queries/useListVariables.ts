/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { listVariables } from '..';
import { variableKeys } from '../keys';

interface Props {
  providerId?: string;
}

export function useListVariables({ providerId }: Props) {
  return useQuery({
    queryKey: variableKeys.list(providerId ?? ''),
    queryFn: () => listVariables(providerId!),
    enabled: Boolean(providerId),
  });
}
