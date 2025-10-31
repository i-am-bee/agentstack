/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { deleteConnector } from '..';
import { connectorKeys } from '../keys';

export function useDeleteConnector() {
  const mutation = useMutation({
    mutationFn: deleteConnector,
    meta: {
      invalidates: [connectorKeys.list()],
      errorToast: {
        title: 'Failed to delete connector.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
