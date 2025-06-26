/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import type { MainContentViewProps } from '@i-am-bee/beeai-ui';
import { MainContentView } from '@i-am-bee/beeai-ui';
import { usePathname } from 'next/navigation';

export function MainContent({ ...props }: MainContentViewProps) {
  const pathname = usePathname();
  const isAgentsRoute = pathname === '/agents';

  return <MainContentView enableToTopButton={isAgentsRoute} showFooter {...props} />;
}
