/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { deleteContext } from '..';
import { contextKeys } from '../keys';

interface Props {
  onMutate?: () => void;
}

export function useDeleteContext({ onMutate }: Props = {}) {
  const mutation = useMutation({
    mutationFn: deleteContext,
    meta: {
      invalidates: [contextKeys.lists()],
      errorToast: {
        title: 'Failed to delete session.',
        includeErrorMessage: true,
      },
    },
    onMutate,
  });

  return mutation;
}
