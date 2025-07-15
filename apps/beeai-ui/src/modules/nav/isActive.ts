/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { NavItem } from './schema';

export function isActive(item: NavItem, pathname: string): boolean {
  return (item.activePathnames ?? []).some((active) => pathname === active || pathname.startsWith(`${active}/`));
}
