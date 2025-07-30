/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import '../styles/style.scss';

import type { Metadata } from 'next';

import { AppLayout } from '#components/layouts/AppLayout.tsx';
import { APP_FAVICON_SVG, APP_NAME, BASE_PATH, FEATURE_FLAGS } from '#utils/constants.ts';
import { parseFeatureFlags } from '#utils/feature-flags.ts';

import Providers from './providers';

const darkModeScript = `
(() => {
  try {
    const html = document.documentElement;
    const storedTheme = window.localStorage.getItem('@i-am-bee/beeai/THEME');
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
      </head>
      <body>
        <Providers featureFlags={parseFeatureFlags(FEATURE_FLAGS)}>
          <AppLayout>{children}</AppLayout>
        </Providers>
      </body>
    </html>
  );
}
