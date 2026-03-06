/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type { streamingMessageSchema } from './schemas';

export type StreamingMessage = z.infer<typeof streamingMessageSchema>;
