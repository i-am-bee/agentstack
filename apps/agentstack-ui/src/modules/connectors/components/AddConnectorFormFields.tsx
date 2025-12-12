/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { TextInput } from '@carbon/react';
import { useId } from 'react';
import { useFormContext } from 'react-hook-form';

import type { AddConnectorForm } from '../types';
import classes from './AddConnectorFormFields.module.scss';

export function AddConnectorFormFields() {
  const id = useId();

  const {
    register,
    formState: { errors },
  } = useFormContext<AddConnectorForm>();

  return (
    <div className={classes.root}>
      <TextInput
        id={`${id}:name`}
        labelText="Name"
        invalid={Boolean(errors.name)}
        invalidText={errors.name?.message}
        {...register('name')}
      />

      <TextInput
        id={`${id}:url`}
        labelText="URL"
        invalid={Boolean(errors.url)}
        invalidText={errors.url?.message}
        {...register('url')}
      />

      <TextInput
        id={`${id}:client-id`}
        labelText="Client ID"
        invalid={Boolean(errors.clientId)}
        invalidText={errors.clientId?.message}
        {...register('clientId', { deps: ['clientSecret'] })}
      />

      <TextInput
        id={`${id}:client-secret`}
        labelText="Client secret"
        invalid={Boolean(errors.clientSecret)}
        invalidText={errors.clientSecret?.message}
        {...register('clientSecret')}
      />
    </div>
  );
}
