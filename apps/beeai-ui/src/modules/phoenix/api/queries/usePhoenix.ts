/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { PHOENIX_SERVER_TARGET, PROD_MODE } from '#utils/constants.ts';

import { phoenixKeys } from '../keys';

export function usePhoenix() {
  const query = useQuery({
    queryKey: phoenixKeys.all(),
    refetchInterval: PROD_MODE ? 5_000 : false,
    enabled: Boolean(PHOENIX_SERVER_TARGET),
    queryFn: () =>
      fetch(PHOENIX_SERVER_TARGET!, { mode: 'no-cors' })
        .then(() => true)
        .catch(() => false),
  });

  return query;
}
