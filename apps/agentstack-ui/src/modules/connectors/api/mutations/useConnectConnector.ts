/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';
import { connectConnector } from '..';

export function useConnectConnector() {
  const mutation = useMutation({
    mutationFn: connectConnector,
    meta: {
      errorToast: {
        title: 'Failed to connect OAuth service.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
