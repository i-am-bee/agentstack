/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import type { ContextPermissionsGrant, GlobalPermissionGrant } from '#api/types.ts';

import { createContextToken } from '..';

export function useCreateContextToken() {
  const mutation = useMutation({
    mutationFn: ({
      contextId,
      globalPermissionGrant,
      contextPermissionGrant,
    }: {
      contextId: string;
      globalPermissionGrant: GlobalPermissionGrant;
      contextPermissionGrant: ContextPermissionsGrant;
    }) => createContextToken(contextId, globalPermissionGrant, contextPermissionGrant),
  });

  return mutation;
}
