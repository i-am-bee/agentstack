/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { matchQuery, MutationCache, QueryCache, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { PropsWithChildren } from 'react';

import { useHandleError } from '#hooks/useHandleError.ts';

import type { HandleError } from './types';

const createQueryClient = ({ handleError }: { handleError: HandleError }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 1000 * 60, // 60 seconds
        gcTime: 1000 * 60 * 60 * 24, // 24 hours
      },
    },
    queryCache: new QueryCache({
      onError: (error, query) => {
        handleError(error, {
          errorToast: query.meta?.errorToast,
        });
      },
    }),
    mutationCache: new MutationCache({
      onError: (error, _variables, _context, mutation) => {
        handleError(error, {
          errorToast: mutation.meta?.errorToast,
        });
      },
      onSuccess: (_data, _variables, _context, mutation) => {
        queryClient.invalidateQueries({
          predicate: (query) =>
            mutation.meta?.invalidates?.some((queryKey) => matchQuery({ queryKey }, query)) ?? false,
        });
      },
    }),
  });

  return queryClient;
};

export function QueryProvider({ children }: PropsWithChildren) {
  const handleError = useHandleError();
  const queryClient = createQueryClient({ handleError });

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
