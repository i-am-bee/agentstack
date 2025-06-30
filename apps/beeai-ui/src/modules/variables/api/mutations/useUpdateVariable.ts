/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { providerKeys } from '#modules/providers/api/keys.ts';

import { updateVariable } from '..';
import { variableKeys } from '../keys';

interface Props {
  onSuccess?: () => void;
}

export function useUpdateVariable({ onSuccess }: Props = {}) {
  const mutation = useMutation({
    mutationFn: updateVariable,
    onSuccess,
    meta: {
      invalidates: [variableKeys.lists(), providerKeys.lists()],
      errorToast: {
        title: 'Failed to update variable.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
