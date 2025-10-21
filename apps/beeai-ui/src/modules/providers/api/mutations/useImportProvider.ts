/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { registerManagedProvider } from '..';
import { providerKeys } from '../keys';

export function useImportProvider() {
  const mutation = useMutation({
    mutationFn: registerManagedProvider,
    meta: {
      invalidates: [providerKeys.lists()],
      errorToast: {
        title: 'Failed to import provider.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
