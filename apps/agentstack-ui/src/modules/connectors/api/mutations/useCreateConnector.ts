/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { createConnector } from '..';
import { connectorKeys } from '../keys';

interface Props {
  onSuccess?: () => void;
}

export function useCreateConnector({ onSuccess }: Props = {}) {
  const mutation = useMutation({
    mutationFn: createConnector,
    onSuccess,
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
