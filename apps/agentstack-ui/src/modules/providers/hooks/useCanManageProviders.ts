/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useApp } from '#contexts/App/index.ts';
import { useUser } from '#modules/users/api/queries/useUser.ts';
import { isUserAdminOrDev } from '#modules/users/utils.ts';

export function useCanManageProviders() {
  const {
    config: { featureFlags },
  } = useApp();
  const { data: user } = useUser();

  const isAdminOrDev = isUserAdminOrDev(user);
  const canManageProviders = Boolean(featureFlags.Providers && isAdminOrDev);

  return canManageProviders;
}
