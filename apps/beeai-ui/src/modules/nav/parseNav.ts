/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type NavItem, navSchema } from './schema';

export function parseNav(data: unknown): NavItem[] {
  const result = navSchema.safeParse(data);

  return result.success ? result.data : [];
}
