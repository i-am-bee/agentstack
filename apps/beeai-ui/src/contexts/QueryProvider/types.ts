/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { QueryKey } from '@tanstack/react-query';

import type { useHandleError } from '#hooks/useHandleError.ts';

export interface QueryMetadata extends Record<string, unknown> {
  errorToast?:
    | false
    | {
        title?: string;
        includeErrorMessage?: boolean;
      };
}

export type HandleError = ReturnType<typeof useHandleError>;

declare module '@tanstack/react-query' {
  interface Register {
    queryMeta: QueryMetadata;
    mutationMeta: QueryMetadata & {
      invalidates?: QueryKey[];
    };
  }
}
