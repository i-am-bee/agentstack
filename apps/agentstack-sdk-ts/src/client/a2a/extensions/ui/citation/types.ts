/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type { citationMetadataSchema, citationSchema } from './schemas';

export type Citation = z.infer<typeof citationSchema>;

export type CitationMetadata = z.infer<typeof citationMetadataSchema>;
