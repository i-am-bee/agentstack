/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { paths } from '#api/schema.js';

export const MAX_FILES = 5;

export const MAX_FILE_SIZE = 100 * 1024 * 1024;

export const FILE_CONTENT_URL = '/api/v1/files/{file_id}/content' satisfies keyof paths;

export const ALL_FILES_CONTENT_TYPE = '*/*';

export const NO_FILES_CONTENT_TYPE = 'none';
