/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { usePathname, useRouter } from 'next/navigation';
import { useCallback } from 'react';

import { UnauthenticatedError } from '#api/errors.ts';
import { getErrorMessage } from '#api/utils.ts';
import type { QueryMetadata } from '#contexts/QueryProvider/types.ts';
import { useToast } from '#contexts/Toast/index.ts';
import { routes } from '#utils/router.ts';

export function useHandleError() {
  const router = useRouter();
  const pathname = usePathname();
  const { addToast } = useToast();

  const handleError = useCallback(
    (error: unknown, options: QueryMetadata = {}) => {
      const { errorToast } = options;

      let errorTitle = 'An error occurred';

      if (error instanceof UnauthenticatedError) {
        router.replace(routes.signIn({ callbackUrl: pathname }));
        errorTitle = error.message || 'You are not authenticated.';
      }
      if (errorToast !== false) {
        const errorMessage = errorToast?.includeErrorMessage ? getErrorMessage(error) : undefined;

        addToast({
          title: errorToast?.title ?? errorTitle,
          subtitle: errorToast?.message,
          apiError: errorMessage,
        });
      } else {
        console.error(error);
      }
    },
    [addToast, pathname, router],
  );

  return handleError;
}
