/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { useSession } from 'next-auth/react';
import { useEffect } from 'react';

export function SessionRefresher() {
  const { update, data: session } = useSession();

  useEffect(() => {
    async function earlyTokenRefresh() {
      console.log('earlyTokenRefresh called');

      update({ ...session, earlyTokenRefresh: true });
    }

    // Refresh on focus/online — low overhead, less flakiness than fixed intervals
    function onFocus() {
      earlyTokenRefresh();
    }
    function onOnline() {
      earlyTokenRefresh();
    }

    window.addEventListener('focus', onFocus);
    window.addEventListener('online', onOnline);

    const timer = setInterval(() => {
      earlyTokenRefresh();
    }, 10_000);

    return () => {
      window.removeEventListener('focus', onFocus);
      window.removeEventListener('online', onOnline);
      if (timer) clearInterval(timer);
    };
  }, [session, update]);

  return null;
}
