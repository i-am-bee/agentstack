/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { createContext } from '..';

export function useCreateContext() {
  const mutation = useMutation({
    mutationFn: createContext,
  });

  return mutation;
}
