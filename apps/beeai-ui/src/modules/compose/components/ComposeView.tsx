/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container } from '#components/layouts/Container.tsx';
import { SplitPanesView } from '#components/SplitPanesView/SplitPanesView.tsx';

import { useCompose } from '../contexts';
import { SequentialSetup } from '../sequential/SequentialSetup';
import { ComposeResult } from './ComposeResult';

export function ComposeView() {
  const { result } = useCompose();

  const sequentialSetup = <SequentialSetup />;

  return (
    <SplitPanesView
      mainContent={<Container size="sm">{sequentialSetup}</Container>}
      leftPane={sequentialSetup}
      rightPane={<ComposeResult />}
      isSplit={Boolean(result)}
    />
  );
}
