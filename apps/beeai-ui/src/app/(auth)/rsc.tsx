/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { redirect } from 'next/navigation';
import { getSession } from 'next-auth/react';

import { OIDC_ENABLED } from '#utils/constants.ts';

export const ensureSession = async () => {
  if (!OIDC_ENABLED) {
    return null;
  }

  const session = await getSession();

  if (!session) {
    redirect('/signin');
  }
  return session;
};
