/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { createContext } from '..';
import { contextKeys } from '../keys';
import type { CreateContextResponse } from '../types';

export function useCreateContext({ onSuccess }: { onSuccess?: (data: CreateContextResponse) => void } = {}) {
  const mutation = useMutation({
    mutationFn: createContext,
    onSuccess,
    meta: {
      invalidates: [contextKeys.lists()],
    },
  });

  return mutation;
}
