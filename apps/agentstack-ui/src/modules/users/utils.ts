/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { User } from './api/types';

export function isUserAdminOrDev(user: User | undefined) {
  if (!user) {
    return false;
  }

  const { role } = user;

  return role === 'admin' || role === 'developer';
}
