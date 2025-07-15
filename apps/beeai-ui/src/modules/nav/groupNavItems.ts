/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { NavItem } from './schema';

type Groups = {
  start: NavItem[];
  end: NavItem[];
};

export function groupNavItems(items: NavItem[]): Groups {
  return {
    start: items.filter((item) => item.position !== 'end'),
    end: items.filter((item) => item.position === 'end'),
  };
}
