/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { usePathname } from 'next/navigation';
import { useEffect, useRef } from 'react';

import { ANALYTICS_APP_NAME } from '@/constants';

export function AnalyticsScript() {
  const pathname = usePathname();
  const skipPageViewCall = useRef(true);

  const isEnabled = Boolean(ANALYTICS_APP_NAME) && isTopWindow();

  // Init config and inject IBM Analytics script
  useEffect(() => {
    if (!isEnabled) return;

    // IBM Analytics config
    window._ibmAnalytics = {
      settings: {
        name: ANALYTICS_APP_NAME,
        isSpa: true,
      },
      trustarc: {
        isCookiePreferencesInstalled: true,
      },
      onLoad: [['ibmStats.pageview', []]], // first pageview on load
    };

    // Digital Data layer
    window.digitalData = {
      page: {
        pageInfo: {
          ibm: { siteId: ANALYTICS_APP_NAME },
          analytics: { category: 'Beeai' },
        },
        category: { primaryCategory: 'PC340' },
      },
    };

    // Inject IBM common script
    document.body.appendChild(
      Object.assign(document.createElement('script'), {
        src: IBM_COMMON_SRC,
        defer: true,
      }),
    );
  }, [isEnabled]);

  useEffect(() => {
    if (!isEnabled) return;
    // Skip the first call since it's handled in onLoad
    if (skipPageViewCall.current) {
      skipPageViewCall.current = false;
      return;
    }
    window.ibmStats?.pageview();
  }, [isEnabled, pathname]);

  return null;
}

const IBM_COMMON_SRC = 'https://1.www.s81c.com/common/stats/ibm-common.js';

// Avoid tracking when embedded in an iframe
function isTopWindow() {
  try {
    return window.self === window.top;
  } catch (e) {
    // Cross-origin iframe
    console.error(e);
    return false;
  }
}

declare global {
  interface Window {
    _ibmAnalytics?: object;
    digitalData?: object;
    ibmStats?: { pageview: () => void };
    _dl?: {
      fn: {
        trustarc: {
          cookiePreferencesClick: () => void;
        };
      };
    };
  }
}
