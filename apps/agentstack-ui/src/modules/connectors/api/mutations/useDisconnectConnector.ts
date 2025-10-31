/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { disconnectConnector } from '..';
import { connectorKeys } from '../keys';

export function useDisconnectConnector() {
  const mutation = useMutation({
    mutationFn: disconnectConnector,
    meta: {
      invalidates: [connectorKeys.list()],
      errorToast: {
        title: 'Failed to disconnect service.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
