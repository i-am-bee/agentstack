/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export { auth as middleware } from '#app/(auth)/auth.ts';

// Read more: https://nextjs.org/docs/app/building-your-application/routing/middleware#matcher
export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|bee.svg|BeeAI-Banner.svg|signin|auth/callback|auth/token-proxy).*)',
  ],
};
