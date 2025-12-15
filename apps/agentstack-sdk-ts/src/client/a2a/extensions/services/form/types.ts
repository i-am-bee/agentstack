/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type { formDemandsSchema, formFulfillmentsSchema } from './schemas';

export type FormDemands = z.infer<typeof formDemandsSchema>;

export type FormFulfillments = z.infer<typeof formFulfillmentsSchema>;
