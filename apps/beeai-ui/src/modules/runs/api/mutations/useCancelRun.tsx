/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { cancelRun } from '..';

export function useCancelRun() {
  const mutation = useMutation({
    mutationFn: cancelRun,
    meta: {
      errorToast: false,
    },
  });

  return mutation;
}
