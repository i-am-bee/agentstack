/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useAutoScroll } from '#hooks/useAutoScroll.ts';

import { AgentOutputBox } from '../components/AgentOutputBox';
import { useHandsOff } from '../contexts/hands-off';

export function HandsOffText() {
  const { agent, output, isPending } = useHandsOff();
  const { ref: autoScrollRef } = useAutoScroll([output]);

  return output ? (
    <div>
      <AgentOutputBox text={output} isPending={isPending} downloadFileName={`${agent.name}-output`} />

      {isPending && <div ref={autoScrollRef} />}
    </div>
  ) : null;
}
