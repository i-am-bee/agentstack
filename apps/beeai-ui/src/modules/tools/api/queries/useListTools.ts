/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { listTools } from '..';
import { toolKeys } from '../keys';

export function useListTools() {
  const query = useQuery({
    queryKey: toolKeys.list(),
    queryFn: listTools,
  });

  return query;
}
