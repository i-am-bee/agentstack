/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';
import { createConnector } from '..';

export function useCreateConnector() {
  const mutation = useMutation({
    mutationFn: createConnector,
    meta: {
      errorToast: {
        title: 'Failed to create OAuth connector.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
