/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMutation } from '@tanstack/react-query';

import type { FileEntity } from '../../types';
import { uploadFile } from '..';
import type { UploadFileResponse } from '../types';

interface Props {
  onMutate?: (variables: UploadFileVariables) => void;
  onSuccess?: (data: UploadFileResponse | undefined, variables: UploadFileVariables) => void;
  onError?: (error: Error, variables: UploadFileVariables) => void;
}

interface UploadFileVariables {
  file: FileEntity;
  contextId: string;
}

export function useUploadFile({ onMutate, onSuccess, onError }: Props = {}) {
  const mutation = useMutation({
    mutationFn: ({ file, contextId }: UploadFileVariables) => uploadFile({ body: { file }, contextId }),
    onMutate,
    onSuccess,
    onError,
    meta: {
      errorToast: {
        title: 'Failed to upload file',
        includeErrorMessage: true,
      },
    },
  });

  return mutation;
}
