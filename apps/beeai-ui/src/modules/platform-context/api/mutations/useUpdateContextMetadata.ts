/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { updateContextMetadata } from '..';
import { contextKeys } from '../keys';

export function useUpdateContextMetadata() {
  const mutation = useMutation({
    mutationFn: updateContextMetadata,
    meta: {
      invalidates: [contextKeys.lists()],
    },
  });

  return mutation;
}
