/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import { MainContent } from '#components/layouts/MainContent.tsx';

import { SourcesPanel } from '../sources/components/SourcesPanel';
export function ChatView({ children }: PropsWithChildren) {
  return (
    <>
      <MainContent limitHeight>{children}</MainContent>

      <SourcesPanel />
    </>
  );
}
