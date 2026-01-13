/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import '#styles/style.scss';

import type { Metadata } from 'next';
import { connection } from 'next/server';

import { AppProvider } from '#contexts/App/AppProvider.tsx';
import { runtimeConfig } from '#contexts/App/runtime-config.ts';
import Providers from '#providers.tsx';
import { APP_FAVICON_SVG, APP_FAVICON_SVG_DARK, BASE_PATH, THEME_STORAGE_KEY } from '#utils/constants.ts';

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
const darkIcon = `${BASE_PATH}${APP_FAVICON_SVG_DARK}`;

export const metadata: Metadata = {
  title: runtimeConfig.appName,
  icons: {
    icon: [{ url: icon }, { url: darkIcon, media: '(prefers-color-scheme: dark)' }],
  },
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  await connection();

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: darkModeScript }} />
      </head>
      <body>
        <AppProvider config={runtimeConfig}>
          <Providers>{children}</Providers>
        </AppProvider>
      </body>
    </html>
  );
}
