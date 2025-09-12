/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from '@carbon/react';

import type { UIAgentMessage } from '#modules/messages/types.ts';
import { getMessageSecret } from '#modules/messages/utils.ts';
import { useAgentRun } from '#modules/runs/contexts/agent-run/index.ts';
import { useAgentSettings } from '#modules/runs/contexts/agent-settings/index.ts';
import type { AgentRequestedApiKeys } from '#modules/runs/contexts/agent-settings/types.ts';

interface Props {
  message: UIAgentMessage;
}

export function MessageSecret({ message }: Props) {
  const secretPart = getMessageSecret(message);
  const { submitSecrets } = useAgentRun();
  const { provideSecrets } = useAgentSettings();

  if (!secretPart) {
    return null;
  }

  const testingSecrets = Object.entries(secretPart.secret.secret_demands).reduce<AgentRequestedApiKeys>(
    (acc, [key]) => ({
      ...acc,
      [key]: { ...secretPart.secret.secret_demands[key], isReady: true, value: 'Some Random Secret' },
    }),
    {},
  );

  return (
    <div>
      Provide secrets for{' '}
      {Object.entries(secretPart.secret.secret_demands)
        .map(([demand, { name, description }]) => `${demand} - ${name}, ${description}`)
        .join(', ')}
      <Button
        onClick={() => {
          provideSecrets(
            Object.entries(secretPart.secret.secret_demands).reduce(
              (acc, [key]) => ({ ...acc, [key]: 'Some Random Secret' }),
              {},
            ),
          );
          submitSecrets(testingSecrets, secretPart.taskId);
        }}
      >
        Submit
      </Button>
    </div>
  );
}
