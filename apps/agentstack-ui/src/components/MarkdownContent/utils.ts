/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { defaultUrlTransform } from 'react-markdown';

import { PLATFORM_FILE_CONTENT_URL_BASE } from '#api/a2a/constants.ts';
import { getFileIdFromFilePlatformUrl } from '#api/a2a/utils.ts';
import { getFileContentUrl } from '#modules/files/utils.ts';

export function urlTransform(value: string): string {
  if (value.startsWith('data:image/')) {
    return value;
  }

  if (value.startsWith(PLATFORM_FILE_CONTENT_URL_BASE)) {
    return getFileContentUrl(getFileIdFromFilePlatformUrl(value));
  }

  return defaultUrlTransform(value);
}
