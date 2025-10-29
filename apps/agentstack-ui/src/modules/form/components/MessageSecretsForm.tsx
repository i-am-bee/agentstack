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
  const { isLastMessage } = useMessages();

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
    submitSecrets(secretPart.taskId, values);
  };

  const isCurrentMessageLast = isLastMessage(message);

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <fieldset disabled={!isCurrentMessageLast} className={classes.root}>
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

        {isCurrentMessageLast && (
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
