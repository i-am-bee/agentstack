/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { useSession } from 'next-auth/react';
import { useEffect } from 'react';

export function TokenRefresher() {
  const { update, data: session } = useSession();

  useEffect(() => {
    const refreshSchedule = session?.refreshSchedule;
    if (!refreshSchedule) {
      return;
    }

    const { refreshAt, checkInterval } = refreshSchedule;

    async function proactiveTokenRefresh() {
      if (!refreshAt || Date.now() / 1000 < refreshAt) {
        return;
      }

      update({ ...session, proactiveTokenRefresh: true });
    }

    function handleRefreshEvent() {
      proactiveTokenRefresh();
    }
    window.addEventListener('focus', handleRefreshEvent);
    window.addEventListener('online', handleRefreshEvent);

    const timer = setInterval(() => {
      proactiveTokenRefresh();
    }, checkInterval * 1000);

    return () => {
      window.removeEventListener('focus', handleRefreshEvent);
      window.removeEventListener('online', handleRefreshEvent);
      if (timer) clearInterval(timer);
    };
  }, [session, update]);

  return null;
}
