/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  readSystemConfigurationRequestSchema,
  readSystemConfigurationResponseSchema,
  systemConfigurationSchema,
  updateSystemConfigurationRequestSchema,
  updateSystemConfigurationResponseSchema,
} from './schemas';

export type SystemConfiguration = z.infer<typeof systemConfigurationSchema>;

export type ReadSystemConfigurationRequest = z.infer<typeof readSystemConfigurationRequestSchema>;
export type ReadSystemConfigurationResponse = z.infer<typeof readSystemConfigurationResponseSchema>;

export type UpdateSystemConfigurationRequest = z.infer<typeof updateSystemConfigurationRequestSchema>;
export type UpdateSystemConfigurationResponse = z.infer<typeof updateSystemConfigurationResponseSchema>;
