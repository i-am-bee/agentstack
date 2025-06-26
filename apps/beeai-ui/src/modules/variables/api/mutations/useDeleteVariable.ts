/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { providerKeys } from '#modules/providers/api/keys.ts';

import { deleteVariable } from '..';
import { variableKeys } from '../keys';

export function useDeleteVariable() {
  const mutation = useMutation({
    mutationFn: deleteVariable,
    meta: {
      invalidates: [variableKeys.lists(), providerKeys.lists()],
      errorToast: {
        title: 'Failed to delete variable.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
