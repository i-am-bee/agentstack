/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import '../styles/style.scss';

import { APP_FAVICON_SVG, BASE_PATH, THEME_STORAGE_KEY } from '@i-am-bee/beeai-ui';
import type { Metadata } from 'next';

import { AnalyticsScript } from '@/components/AnalyticsScript/AnalyticsScript';
import { APP_NAME } from '@/constants';
import AppLayout from '@/layouts/AppLayout';

import Providers from './providers';

const darkModeScript = `
(() => {
  try {
    const html = document.documentElement;
    const storedTheme = window.localStorage.getItem('${THEME_STORAGE_KEY}');
    const theme = typeof storedTheme === 'string' ? JSON.parse(storedTheme) : 'System'; 
    const isDarkMode = theme === 'Dark' || (theme === 'System' && window.matchMedia('(prefers-color-scheme: dark)').matches);

    if (isDarkMode) {
      html.classList.add('cds--g90');
      html.classList.remove('cds--white');
    } else {
      html.classList.add('cds--white');
      html.classList.remove('cds--g90');
    }
  } catch (error) {}
})();
`;

const icon = `${BASE_PATH}${APP_FAVICON_SVG}`;

export const metadata: Metadata = {
  title: APP_NAME,
  icons: {
    icon: icon,
    shortcut: icon,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: darkModeScript }} />

        <AnalyticsScript />
      </head>
      <body>
        <Providers>
          <AppLayout>{children}</AppLayout>
        </Providers>
      </body>
    </html>
  );
}
