/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { createRunStream } from '..';

export function useCreateRunStream() {
  const mutation = useMutation({
    mutationFn: createRunStream,
    meta: {
      errorToast: false,
    },
  });

  return mutation;
}
