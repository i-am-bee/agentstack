/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import '#styles/style.scss';

import type { Metadata } from 'next';

import { AppLayout } from '#components/layouts/AppLayout.tsx';
import { APP_NAME } from '#utils/constants.ts';

export const metadata: Metadata = {
  title: APP_NAME,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <AppLayout>{children}</AppLayout>;
}
