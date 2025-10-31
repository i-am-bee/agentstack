/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CommonHeader } from '#components/layouts/CommonHeader.tsx';
import { HeaderLayout } from '#components/layouts/HeaderLayout.tsx';

export default function CommonLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <HeaderLayout>
      <CommonHeader />

      {children}
    </HeaderLayout>
  );
}
