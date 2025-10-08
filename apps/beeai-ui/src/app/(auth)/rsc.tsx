/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use server';
import { cookies } from 'next/headers';
import { getToken } from 'next-auth/jwt';

import { runtimeConfig } from '#contexts/App/runtime-config.ts';

import { auth, AUTH_COOKIE_NAME } from './auth';

export const ensureToken = async (request: Request) => {
  if (!runtimeConfig.isAuthEnabled) {
    return null;
  }

  const session = await auth();
  if (!session) {
    return null;
  }

  // Ensure we have auth cookie, because it's not included in RSC requests
  if (!request.headers.get('cookie')?.includes(`${AUTH_COOKIE_NAME}=`)) {
    const cookieStore = await cookies();
    request.headers.set('cookie', cookieStore.toString());
  }

  const token = await getToken({ req: request, cookieName: AUTH_COOKIE_NAME, secret: process.env.NEXTAUTH_SECRET });

  // Don't manually update cookies - let the client handle its own refresh
  return token;
};
