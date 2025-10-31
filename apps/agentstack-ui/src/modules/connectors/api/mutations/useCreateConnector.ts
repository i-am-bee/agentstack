/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { createConnector } from '..';
import { connectorKeys } from '../keys';

export function useCreateConnector() {
  const mutation = useMutation({
    mutationFn: createConnector,
    meta: {
      invalidates: [connectorKeys.list()],
      errorToast: {
        title: 'Failed to create connector.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
