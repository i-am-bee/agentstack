/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { listConnectorPresets } from '..';
import { connectorKeys } from '../keys';

export function useListConnectorPresets() {
  const query = useQuery({
    queryKey: connectorKeys.presetsList(),
    queryFn: listConnectorPresets,
  });

  return query;
}
