/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { PlayFilledAlt } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import { useForm } from 'react-hook-form';

import { InputBar } from '../components/InputBar';
import { useHandsOff } from '../contexts/hands-off';
import { useFileUpload } from '../files/contexts';

export function HandsOffInput() {
  const { isPending, onSubmit } = useHandsOff();
  const { isPending: isFileUploadPending } = useFileUpload();

  const form = useForm<FormValues>({
    mode: 'onChange',
    defaultValues: {},
  });

  const { register, handleSubmit, watch, reset } = form;

  const inputValue = watch('input');

  const isSubmitDisabled = isPending || isFileUploadPending || !inputValue;

  return (
    <InputBar
      onSubmit={() => {
        handleSubmit(async ({ input }) => {
          await onSubmit(input);

          reset();
        })();
      }}
      isSubmitDisabled={isSubmitDisabled}
      inputProps={{
        placeholder: 'Write the agent prompt here',
        ...register('input', { required: true }),
      }}
    >
      <Button type="submit" renderIcon={PlayFilledAlt} size="sm" disabled={isSubmitDisabled}>
        Run
      </Button>
    </InputBar>
  );
}

export interface FormValues {
  input: string;
}
