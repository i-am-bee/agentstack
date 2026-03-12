/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type { networkProviderLocationSchema } from './schemas';

export type NetworkProviderLocation = z.infer<typeof networkProviderLocationSchema>;
