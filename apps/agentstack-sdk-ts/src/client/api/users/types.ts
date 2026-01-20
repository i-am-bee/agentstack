/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type { readUserRequestSchema, readUserResponseSchema, userSchema } from './schemas';

export enum UserRole {
  Admin = 'admin',
  Developer = 'developer',
  User = 'user',
}

export type User = z.infer<typeof userSchema>;

export type ReadUserRequest = z.infer<typeof readUserRequestSchema>;
export type ReadUserResponse = z.infer<typeof readUserResponseSchema>;
