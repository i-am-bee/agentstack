/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback } from 'react';

import { getErrorMessage } from '#api/utils.ts';
import type { QueryMetadata } from '#contexts/QueryProvider/types.ts';
import { useToast } from '#contexts/Toast/index.ts';

export function useHandleError() {
  const { addToast } = useToast();

  const handleError = useCallback(
    (error: unknown, options: QueryMetadata = {}) => {
      const { errorToast } = options;

      if (errorToast !== false) {
        const errorMessage = errorToast?.includeErrorMessage ? getErrorMessage(error) : undefined;

        addToast({
          title: errorToast?.title ?? 'An error occured',
          subtitle: errorMessage,
        });
      } else {
        console.error(error);
      }
    },
    [addToast],
  );

  return handleError;
}
