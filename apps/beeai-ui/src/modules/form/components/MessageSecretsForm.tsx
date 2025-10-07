/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, PasswordInput } from '@carbon/react';
import { useId, useMemo } from 'react';
import { useForm } from 'react-hook-form';

import { useMessages } from '#modules/messages/contexts/Messages/index.ts';
import type { UIAgentMessage } from '#modules/messages/types.ts';
import { getMessageSecret } from '#modules/messages/utils.ts';
import { useAgentRun } from '#modules/runs/contexts/agent-run/index.ts';
import type { AgentRequestSecrets } from '#modules/runs/contexts/agent-secrets/types.ts';
import { useUpdateVariables } from '#modules/variables/api/mutations/useUpdateVariables.ts';

import classes from './MessageSecretsForm.module.scss';

interface Props {
  message: UIAgentMessage;
}

export function MessageSecretsForm({ message }: Props) {
  const id = useId();
  const secretPart = getMessageSecret(message);
  const { submitSecrets } = useAgentRun();
  const { mutate: updateVariables } = useUpdateVariables();
  const { messages } = useMessages();

  const { register, handleSubmit } = useForm({ mode: 'onChange' });

  const secretDemandsEntries = useMemo(
    () => (secretPart ? Object.entries(secretPart.secret.secret_demands) : []),
    [secretPart],
  );

  if (!secretPart) {
    return null;
  }

  const onSubmit = async (values: FormValues) => {
    updateVariables({ variables: values });

    const secretsFulfillment = secretDemandsEntries.reduce<AgentRequestSecrets>((acc, [key, demand]) => {
      const value = values[key];
      if (value) {
        acc[key] = { ...demand, isReady: true, value };
      }
      return acc;
    }, {});
    submitSecrets(secretsFulfillment, secretPart.taskId);
  };

  const isLastMessage = messages.at(-1)?.id === message.id;

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <fieldset disabled={!isLastMessage} className={classes.root}>
        {secretDemandsEntries.map(([key, { name, description }], idx) => {
          return (
            <div key={key} className={classes.demand}>
              <p>{description}</p>
              <PasswordInput
                id={`${id}:${key}`}
                labelText={name}
                {...register(key, { required: true })}
                autoFocus={idx === 0}
              />
            </div>
          );
        })}

        {isLastMessage && (
          <Button size="md" type="submit">
            Submit
          </Button>
        )}
      </fieldset>
    </form>
  );
}

interface FormValues {
  [key: string]: string;
}
