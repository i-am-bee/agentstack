/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { usePathname } from 'next/navigation';

import type { MainContentViewProps } from '#components/MainContentView/MainContentView.tsx';
import { MainContentView } from '#components/MainContentView/MainContentView.tsx';
import { routes } from '#utils/router.ts';

export function MainContent({ ...props }: MainContentViewProps) {
  const pathname = usePathname();
  const isAgentsRoute = pathname === routes.agents();

  return <MainContentView enableToTopButton={isAgentsRoute} {...props} />;
}
