/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use server';

import { isHttpError } from 'agentstack-sdk';
import { cookies } from 'next/headers';
import { notFound, redirect } from 'next/navigation';
import { getToken } from 'next-auth/jwt';

import { isUnauthenticatedError } from '#api/errors.ts';
import { logErrorDetails } from '#api/utils.ts';
import { runtimeConfig } from '#contexts/App/runtime-config.ts';
import { routes } from '#utils/router.ts';

import { auth, AUTH_COOKIE_NAME } from './auth';

export async function ensureToken(request: Request) {
  const { isAuthEnabled } = runtimeConfig;

  if (!isAuthEnabled) {
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

  return token;
}

export async function handleApiError(error: unknown) {
  logErrorDetails(error);

  if (isUnauthenticatedError(error)) {
    redirect(routes.signIn());
  } else if (isHttpError(error, 404) || isHttpError(error, 422)) {
    notFound();
  }
}
