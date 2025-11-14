/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { User } from './api/types';

export function isUserAdmin(user: User | undefined) {
  return user?.role === 'admin';
}
