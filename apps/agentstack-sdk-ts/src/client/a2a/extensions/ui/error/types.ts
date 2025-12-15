/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type { errorGroupSchema, errorMetadataSchema, errorSchema } from './schemas';

export type Error = z.infer<typeof errorSchema>;

export type ErrorGroup = z.infer<typeof errorGroupSchema>;

export type ErrorMetadata = z.infer<typeof errorMetadataSchema>;
