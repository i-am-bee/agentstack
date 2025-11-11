/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { listConnectors } from '..';
import { connectorKeys } from '../keys';

export function useListConnectors() {
  const query = useQuery({
    queryKey: connectorKeys.list(),
    queryFn: listConnectors,
  });

  return query;
}
