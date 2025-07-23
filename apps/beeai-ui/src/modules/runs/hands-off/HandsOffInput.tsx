/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { PlayFilledAlt } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import { useForm } from 'react-hook-form';

import { useFileUpload } from '#modules/files/contexts/index.ts';

import { InputBar } from '../components/InputBar';
import { useAgentRun } from '../contexts/agent-run';

export function HandsOffInput() {
  const { agent, isPending, run } = useAgentRun();
  const { isPending: isFileUploadPending } = useFileUpload();

  const form = useForm<FormValues>({
    mode: 'onChange',
    defaultValues: {},
  });

  const { register, handleSubmit, watch, reset } = form;

  const inputValue = watch('input');

  const {
    ui: { prompt_suggestions },
  } = agent;
  const isSubmitDisabled = isPending || isFileUploadPending || !inputValue;

  return (
    <InputBar
      promptSuggestions={prompt_suggestions}
      onSubmit={() => {
        handleSubmit(async ({ input }) => {
          await run(input);

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
