/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { updateContext } from '..';
import { contextKeys } from '../keys';

export function useUpdateContext() {
  const mutation = useMutation({
    mutationFn: updateContext,
    meta: {
      invalidates: [contextKeys.lists()],
    },
  });

  return mutation;
}
