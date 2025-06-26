/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { deleteFile } from '..';

export function useDeleteFile() {
  const mutation = useMutation({
    mutationFn: deleteFile,
  });

  return mutation;
}
