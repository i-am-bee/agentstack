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

export function useUpdateVariable({ onSuccess }: Props = {}) {
  const mutation = useMutation({
    mutationFn: ({ key, value }: { key: string; value: string | null }) =>
      updateVariables({ variables: { [key]: value } }),
    onSuccess,
    meta: {
      invalidates: [variableKeys.lists()],
      errorToast: {
        title: 'Failed to update variable.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
