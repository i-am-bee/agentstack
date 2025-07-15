/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

const navItemSchema = z.object({
  label: z.string(),
  url: z.string(),
  activePathnames: z.array(z.string()).optional(),
  isExternal: z.boolean().optional(),
  target: z.enum(['_self', '_blank']).optional(),
  position: z.enum(['start', 'end']).optional(),
});

export const navSchema = z.array(navItemSchema);

export type NavItem = z.infer<typeof navItemSchema>;
