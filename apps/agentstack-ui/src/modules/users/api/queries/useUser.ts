/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { readUser } from '..';
import { userKeys } from '../keys';

export function useUser() {
  const query = useQuery({
    queryKey: userKeys.detail(),
    queryFn: readUser,
    staleTime: Infinity,
    meta: {
      errorToast: { title: 'Failed to load user details.', includeErrorMessage: true },
    },
  });

  return query;
}
