/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type { createUserFeedbackRequestSchema, createUserFeedbackResponseSchema } from './schemas';

export type CreateUserFeedbackRequest = z.infer<typeof createUserFeedbackRequestSchema>;
export type CreateUserFeedbackResponse = z.infer<typeof createUserFeedbackResponseSchema>;
