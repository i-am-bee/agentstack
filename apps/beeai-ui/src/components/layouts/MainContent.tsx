/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { MainContentViewProps } from '#components/MainContentView/MainContentView.tsx';
import { MainContentView } from '#components/MainContentView/MainContentView.tsx';

export function MainContent({ ...props }: MainContentViewProps) {
  return <MainContentView {...props} />;
}
