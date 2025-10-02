/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { providerKeys } from '#modules/providers/api/keys.ts';

import { deleteProviderVariable } from '..';
import { providerVariableKeys } from '../keys';

export function useDeleteProviderVariable() {
  const mutation = useMutation({
    mutationFn: deleteProviderVariable,
    meta: {
      invalidates: [providerVariableKeys.lists(), providerKeys.lists()],
      errorToast: {
        title: 'Failed to delete variable.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
