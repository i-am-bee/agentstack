/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

const navItemSchema = z.object({
  label: z.string(),
  url: z.union([z.string().url(), z.literal('/')]),
  isActive: z.boolean().optional(),
  isExternal: z.boolean().optional(),
  position: z.enum(['start', 'end']).optional(),
});

export const navSchema = z.array(navItemSchema);

export type NavItem = z.infer<typeof navItemSchema>;
