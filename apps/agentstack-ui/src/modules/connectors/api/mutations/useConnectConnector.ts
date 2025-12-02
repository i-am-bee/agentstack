/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { connectConnector } from '..';
import { connectorKeys } from '../keys';

export function useConnectConnector() {
  const mutation = useMutation({
    mutationFn: connectConnector,
    meta: {
      invalidates: [connectorKeys.list()],
      errorToast: {
        title: 'Failed to connect service.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
