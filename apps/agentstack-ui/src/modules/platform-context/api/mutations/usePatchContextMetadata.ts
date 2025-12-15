/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { patchContextMetadata } from '..';
import { contextKeys } from '../keys';

export function usePatchContextMetadata() {
  const mutation = useMutation({
    mutationFn: patchContextMetadata,
    meta: {
      invalidates: [contextKeys.lists()],
    },
  });

  return mutation;
}
