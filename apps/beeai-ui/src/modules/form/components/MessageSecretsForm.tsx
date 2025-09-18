/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, TextInput } from '@carbon/react';
import { useId } from 'react';
import { useForm } from 'react-hook-form';

import type { UIAgentMessage } from '#modules/messages/types.ts';
import { getMessageSecret } from '#modules/messages/utils.ts';
import { useAgentRun } from '#modules/runs/contexts/agent-run/index.ts';
import { useAgentSettings } from '#modules/runs/contexts/agent-settings/index.ts';
import type { AgentRequestSecrets } from '#modules/runs/contexts/agent-settings/types.ts';

import classes from './MessageSecretsForm.module.scss';

interface Props {
  message: UIAgentMessage;
}

export function MessageSecretsForm({ message }: Props) {
  const id = useId();
  const secretPart = getMessageSecret(message);
  const { submitSecrets } = useAgentRun();
  const { storeSecrets } = useAgentSettings();

  const { register } = useForm({ mode: 'onChange' });

  if (!secretPart) {
    return null;
  }

  const testingSecrets = Object.entries(secretPart.secret.secret_demands).reduce<AgentRequestSecrets>(
    (acc, [key]) => ({
      ...acc,
      [key]: { ...secretPart.secret.secret_demands[key], isReady: true, value: 'Some Random Secret' },
    }),
    {},
  );

  return (
    <div className={classes.root}>
      {Object.entries(secretPart.secret.secret_demands).map(([demand, { name, description }], idx) => {
        const key = `${name}${idx}`;
        return (
          <div key={key} className={classes.demand}>
            <p>{description}</p>
            <TextInput id={`${id}:${key}`} labelText={name} {...register(demand, { required: true })} />
          </div>
        );
      })}

      <Button
        size="sm"
        onClick={() => {
          storeSecrets(
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
