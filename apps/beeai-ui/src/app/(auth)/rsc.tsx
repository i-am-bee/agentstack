/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { redirect } from 'next/navigation';

import { OIDC_ENABLED } from '#utils/constants.ts';
import { routes } from '#utils/router.ts';

import { auth } from './auth';

export const ensureSession = async () => {
  if (!OIDC_ENABLED) {
    return null;
  }

  const session = await auth();

  if (!session) {
    redirect(routes.login());
  }
  return session;
};
