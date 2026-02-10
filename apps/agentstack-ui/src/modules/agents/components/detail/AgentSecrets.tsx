/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, PasswordInput, TextInputSkeleton } from '@carbon/react';
import { useEffect, useId } from 'react';
import type { SubmitHandler } from 'react-hook-form';
import { useForm } from 'react-hook-form';

import { NoItemsMessage } from '#components/NoItemsMessage/NoItemsMessage.tsx';
import { useAgentSecrets } from '#modules/runs/contexts/agent-secrets/index.ts';
import { useUpdateVariables } from '#modules/variables/api/mutations/useUpdateVariables.ts';

import classes from './AgentSecrets.module.scss';

type SecretsForm = Record<string, string>;

export function AgentSecrets() {
  const id = useId();
  const { demandedSecrets, isPendingVariables } = useAgentSecrets();

  const hasSecrets = demandedSecrets.length > 0;

  const defaultValues = demandedSecrets.reduce<SecretsForm>((acc, secret) => {
    acc[secret.key] = secret.isReady ? secret.value : '';
    return acc;
  }, {});

  const {
    register,
    handleSubmit,
    reset,
    formState: { isDirty, isValid },
  } = useForm<SecretsForm>({
    defaultValues,
  });

  useEffect(() => {
    if (!isPendingVariables) {
      reset(defaultValues);
    }
  }, [defaultValues, isPendingVariables, reset]);

  const { mutateAsync: updateVariables } = useUpdateVariables();

  const onSubmit: SubmitHandler<SecretsForm> = async (data) => {
    updateVariables({ variables: data });
  };

  return (
    <div className={classes.root}>
      {hasSecrets ? (
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className={classes.secrets}>
            {demandedSecrets.map(({ key, description }) => (
              <div key={key}>
                <strong>{key}</strong>
                {!isPendingVariables ? (
                  <PasswordInput
                    id={`${id}:${key}`}
                    size="lg"
                    labelText={description}
                    placeholder="Add secret"
                    showPasswordLabel={`Show ${key}`}
                    hidePasswordLabel={`Hide ${key}`}
                    {...register(key)}
                  />
                ) : (
                  <TextInputSkeleton />
                )}
              </div>
            ))}
          </div>

          <hr />

          <div className={classes.buttons}>
            <Button type="submit" kind="tertiary" className={classes.button} disabled={!isDirty || !isValid}>
              Save changes
            </Button>
          </div>
        </form>
      ) : (
        <NoItemsMessage message="This agent does not have any secrets" />
      )}
    </div>
  );
}
