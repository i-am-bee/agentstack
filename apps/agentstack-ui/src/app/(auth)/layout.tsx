/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import '#styles/style.scss';

import { SigninLayout } from '#components/layouts/SigninLayout.tsx';

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <SigninLayout>{children}</SigninLayout>;
}
