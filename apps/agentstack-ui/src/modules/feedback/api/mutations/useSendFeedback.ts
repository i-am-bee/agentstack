/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { sendFeedback } from '..';

export function useSendFeedback() {
  const mutation = useMutation({
    mutationFn: sendFeedback,
    meta: {
      errorToast: {
        title: 'Failed to send feedback.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
