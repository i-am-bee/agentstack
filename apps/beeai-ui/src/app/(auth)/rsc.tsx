/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { redirect } from 'next/navigation';
import type { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

import { OIDC_ENABLED } from '#utils/constants.ts';
import { routes } from '#utils/router.ts';

import { auth, AUTH_COOKIE_NAME } from './auth';

export const ensureToken = async (request: NextRequest) => {
  if (!OIDC_ENABLED) {
    return null;
  }

  const session = await auth();
  if (!session) {
    redirect(routes.signIn());
  }

  const token = await getToken({ req: request, cookieName: AUTH_COOKIE_NAME, secret: process.env.NEXTAUTH_SECRET });

  if (!token) {
    redirect(routes.signIn());
  }
  return token;
};
