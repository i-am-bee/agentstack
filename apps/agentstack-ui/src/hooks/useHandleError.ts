/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
import { useRouter } from 'next/navigation';
import { useCallback } from 'react';

import { UnauthenticatedError } from '#api/errors.ts';
import { getErrorMessage } from '#api/utils.ts';
import type { QueryMetadata } from '#contexts/QueryProvider/types.ts';
import { useToast } from '#contexts/Toast/index.ts';
import { isNotNull } from '#utils/helpers.ts';
import { routes } from '#utils/router.ts';

export function useHandleError() {
  const router = useRouter();
  const { addToast } = useToast();

  const handleError = useCallback(
    (error: unknown, options: QueryMetadata = {}) => {
      const { errorToast } = options;

      if (error instanceof UnauthenticatedError) {
        const callbackUrl = window ? window.location.pathname + window.location.search : undefined;
        router.replace(routes.signIn({ callbackUrl }));
        console.error(error);
      } else if (errorToast !== false) {
        const errorMessage = errorToast?.includeErrorMessage ? getErrorMessage(error) : undefined;

        addToast({
          kind: 'error',
          title: errorToast?.title ?? 'An error occurred',
          message: [errorToast?.message, errorMessage].filter(isNotNull).join('\n\n'),
          renderMarkdown: true,
        });
      } else {
        console.error(error);
      }
    },
    [addToast, router],
  );

  return handleError;
}
