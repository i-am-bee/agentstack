/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { HeaderLayout } from '#components/layouts/HeaderLayout.tsx';
import { AgentHeader } from '#modules/agents/components/detail/AgentHeader.tsx';

export default function RunLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <HeaderLayout>
      <AgentHeader />

      {children}
    </HeaderLayout>
  );
}
