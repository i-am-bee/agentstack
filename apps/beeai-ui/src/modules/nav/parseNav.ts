/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type NavItem, navSchema } from './schema';

export function parseNav(data: string | undefined): NavItem[] {
  if (!data) {
    return [];
  }

  try {
    const json = JSON.parse(data);
    return navSchema.parse(json);
  } catch {
    return [];
  }
}
