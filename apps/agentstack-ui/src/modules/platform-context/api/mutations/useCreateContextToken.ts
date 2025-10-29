/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { createContextToken } from '..';

export function useCreateContextToken() {
  const mutation = useMutation({
    mutationFn: createContextToken,
  });

  return mutation;
}
