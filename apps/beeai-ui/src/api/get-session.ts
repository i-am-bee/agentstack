/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use server';

import { cookies } from 'next/headers';
import type { NextRequest } from 'next/server';

import { auth } from '#auth.ts';

// workaround for https://github.com/nextauthjs/next-auth/issues/11076
export async function getCurrentSession(request?: NextRequest | Request) {
  const session = await auth();
  const cookieStore = await cookies();
  if (request) {
    try {
      cookieStore.set({
        name: 'beeai-platform',
        value: session?.access_token || '',
        httpOnly: true,
        path: '/',
        secure: true,
        sameSite: 'lax',
      });
    } catch (err) {
      console.error(JSON.stringify(err.message));
    }
  }
  return session;
}
