/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { providerKeys } from '#modules/providers/api/keys.ts';

import { updateProviderVariable } from '..';
import { providerVariableKeys } from '../keys';

interface Props {
  onSuccess?: () => void;
}

export function useUpdateProviderVariable({ onSuccess }: Props = {}) {
  const mutation = useMutation({
    mutationFn: updateProviderVariable,
    onSuccess,
    meta: {
      invalidates: [providerVariableKeys.lists(), providerKeys.lists()],
      errorToast: {
        title: 'Failed to update variable.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
