/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import { previewProviderBuild } from '..';

export function usePreviewProviderBuild() {
  const mutation = useMutation({
    mutationFn: previewProviderBuild,
    meta: {
      errorToast: {
        title: 'Failed to preview provider build.',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
