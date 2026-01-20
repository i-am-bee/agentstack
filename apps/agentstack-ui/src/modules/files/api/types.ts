/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CreateFileRequest } from 'agentstack-sdk';

import type { FileEntity } from '../types';

export type UploadFileParams = Omit<CreateFileRequest, 'file'> & { file: FileEntity };
