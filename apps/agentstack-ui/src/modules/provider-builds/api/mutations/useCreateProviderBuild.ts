/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { createProviderBuild } from '..';

export function useCreateProviderBuild() {
  const mutation = useMutation({
    mutationFn: createProviderBuild,
    meta: {
      errorToast: {
        title: 'Failed to create provider build.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
