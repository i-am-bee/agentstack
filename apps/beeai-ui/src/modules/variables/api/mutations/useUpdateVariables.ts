/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { updateVariables } from '..';
import { variableKeys } from '../keys';

interface Props {
  onSuccess?: () => void;
}

export function useUpdateVariables({ onSuccess }: Props = {}) {
  const mutation = useMutation({
    mutationFn: updateVariables,
    onSuccess,
    meta: {
      invalidates: [variableKeys.lists()],
      errorToast: {
        title: 'Failed to update variables.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
