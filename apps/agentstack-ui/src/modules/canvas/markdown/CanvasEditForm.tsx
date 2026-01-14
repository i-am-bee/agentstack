/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Send } from '@carbon/icons-react';
import { IconButton, TextInput } from '@carbon/react';
import { useId } from 'react';
import { useForm } from 'react-hook-form';

import classes from './CanvasEditForm.module.scss';

interface Props {
  onSubmit: (description: string) => void;
}

export function CanvasEditForm({ onSubmit }: Props) {
  const id = useId();

  const {
    handleSubmit,
    register,
    formState: { isValid },
  } = useForm<{ input: string }>();

  return (
    <form className={classes.form} onSubmit={handleSubmit(({ input }) => onSubmit(input))}>
      <div className={classes.content}>
        <TextInput
          placeholder="How do you want to change it?"
          id={id}
          labelText="Edit instructions"
          autoFocus
          size="sm"
          {...register('input', { required: true })}
        />
        <IconButton label="Ask agent" kind="ghost" size="sm" type="submit" disabled={!isValid}>
          <Send />
        </IconButton>
      </div>
    </form>
  );
}
