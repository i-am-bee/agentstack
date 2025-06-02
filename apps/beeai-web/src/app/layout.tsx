/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import '../styles/style.scss';

import type { Metadata } from 'next';

import AppLayout from '@/layouts/AppLayout';

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

export const metadata: Metadata = {
  title: 'BeeAI',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" type="image/svg+xml" href="/bee.svg" />

        <script dangerouslySetInnerHTML={{ __html: darkModeScript }} />
      </head>
      <body>
        <Providers>
          <AppLayout>{children}</AppLayout>
        </Providers>
      </body>
    </html>
  );
}
