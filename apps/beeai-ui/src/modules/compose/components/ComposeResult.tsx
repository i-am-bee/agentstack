/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useAutoScroll } from '#hooks/useAutoScroll.ts';
import { AgentOutputBox } from '#modules/runs/components/AgentOutputBox.tsx';

import { useCompose } from '../contexts';
import { ComposeStatus } from '../contexts/compose-context';

export function ComposeResult() {
  const { result, status } = useCompose();
  const { ref: autoScrollRef } = useAutoScroll([result]);

  const isPending = status === ComposeStatus.InProgress;

  return (
    <>
      <AgentOutputBox text={result} isPending={isPending} />

      <div ref={autoScrollRef} />
    </>
  );
}
