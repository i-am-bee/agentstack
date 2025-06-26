/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import type { QueryMetadata } from '#contexts/QueryProvider/types.ts';

import { listVariables } from '..';
import { variableKeys } from '../keys';

interface Props {
  errorToast?: QueryMetadata['errorToast'];
  retry?: boolean;
}

export function useListVariables({ errorToast, retry }: Props = {}) {
  const query = useQuery({
    queryKey: variableKeys.list(),
    queryFn: listVariables,
    retry,
    meta: {
      errorToast,
    },
  });

  return query;
}
