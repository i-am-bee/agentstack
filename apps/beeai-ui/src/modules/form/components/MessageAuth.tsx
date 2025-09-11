/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from '@carbon/react';
import { useCallback } from 'react';

import type { UIAgentMessage } from '#modules/messages/types.ts';
import { getMessageAuth } from '#modules/messages/utils.ts';
import { useAgentRun } from '#modules/runs/contexts/agent-run/index.ts';

interface Props {
  message: UIAgentMessage;
}

export function MessageAuth({ message }: Props) {
  const authPart = getMessageAuth(message);
  const { startAuth } = useAgentRun();

  const onHandleAuth = useCallback(() => {
    if (!authPart) {
      return;
    }

    startAuth(authPart.url, authPart.taskId);
  }, [startAuth, authPart]);

  if (!authPart) {
    return null;
  }

  return (
    <Button onClick={onHandleAuth} size="md">
      Authorize
    </Button>
  );
}
