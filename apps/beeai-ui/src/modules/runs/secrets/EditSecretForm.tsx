/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, PasswordInput } from '@carbon/react';
import { useId } from 'react';
import { useForm } from 'react-hook-form';

import type { AgentSecret } from '../contexts/agent-secrets/types';
import classes from './EditSecretForm.module.scss';

interface Props {
  secret: AgentSecret;
  updateSecret: (key: string, value: string) => void;
  onSuccess?: () => void;
}

export function EditSecretForm({ secret, updateSecret, onSuccess }: Props) {
  const id = useId();

  const { key } = secret;

  const {
    register,
    handleSubmit,
    formState: { isDirty, isValid },
  } = useForm<FormValues>({
    defaultValues: {
      value: secret.isReady ? secret.value : '',
    },
  });

  const onSubmit = ({ value }: FormValues) => {
    updateSecret(key, value);
    onSuccess?.();
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
      </div>

      <Button type="submit" className={classes.button} disabled={!isDirty || !isValid}>
        Submit
      </Button>
    </form>
  );
}

interface FormValues {
  value: string;
}
