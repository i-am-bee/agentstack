/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, PasswordInput } from '@carbon/react';
import { useId } from 'react';
import type { SubmitHandler } from 'react-hook-form';
import { useForm } from 'react-hook-form';

import type { AgentSecret } from '#modules/runs/contexts/agent-secrets/types.ts';
import { useUpdateVariable } from '#modules/variables/api/mutations/useUpdateVariable.ts';

import { useRevokeSecret } from '../hooks/useRevokeSecret';
import type { EditSecretForm } from '../types';
import classes from './EditSecretForm.module.scss';

interface Props {
  secret: AgentSecret;
  onSuccess?: () => void;
}

export function EditSecretForm({ secret, onSuccess }: Props) {
  const id = useId();

  const { revokeSecret } = useRevokeSecret({ onSuccess });

  const { key, isReady } = secret;

  const { mutate: updateVariable } = useUpdateVariable({ onSuccess });

  const {
    register,
    handleSubmit,
    formState: { isDirty, isValid },
  } = useForm<EditSecretForm>({
    defaultValues: {
      value: secret.isReady ? secret.value : '',
    },
  });

  const onSubmit: SubmitHandler<EditSecretForm> = ({ value }) => {
    updateVariable({ key, value });
  };

  return (
    <form className={classes.root} onSubmit={handleSubmit(onSubmit)}>
      <div className={classes.group}>
        <PasswordInput
          id={`${id}:api-key`}
          size="lg"
          labelText="API Key"
          data-modal-initial-focus
          showPasswordLabel="Show API Key"
          hidePasswordLabel="Hide API Key"
          {...register('value', { required: true })}
        />
        {isReady && (
          <Button kind="danger--ghost" size="sm" className={classes.buttonRevoke} onClick={() => revokeSecret(secret)}>
            Delete key
          </Button>
        )}
      </div>

      <Button type="submit" className={classes.button} disabled={!isDirty || !isValid}>
        Submit
      </Button>
    </form>
  );
}
