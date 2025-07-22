/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { Send, StopOutlineFilled } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import { memo, useCallback, useRef } from 'react';
import { FormProvider, useForm } from 'react-hook-form';

import { useFileUpload } from '#modules/files/contexts/index.ts';

import type { InputBarFormHandle } from '../components/InputBar';
import { InputBar } from '../components/InputBar';
import { useAgentRun } from '../contexts/agent-run';
// import { ChatSettings } from './ChatSettings';
import { ChatDefaultTools } from './constants';

interface Props {
  onMessageSubmit?: () => void;
}

export const ChatInput = memo(function ChatInput({ onMessageSubmit }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<InputBarFormHandle>(null);

  const { isPending, run, cancel } = useAgentRun();
  const { isPending: isFileUploadPending } = useFileUpload();

  const form = useForm<ChatFormValues>({
    mode: 'onChange',
    defaultValues: {
      tools: ChatDefaultTools,
    },
  });

  const { register, watch, handleSubmit } = form;

  const resetForm = useCallback(() => {
    formRef.current?.resetForm();
  }, []);

  const inputValue = watch('input');

  const isSubmitDisabled = isPending || isFileUploadPending || !inputValue;

  return (
    <FormProvider {...form}>
      <div ref={containerRef}>
        <InputBar
          onSubmit={() => {
            handleSubmit(async ({ input }) => {
              onMessageSubmit?.();
              resetForm();

              await run(input);
            })();
          }}
          isSubmitDisabled={isSubmitDisabled}
          // TODO: The API does not yet support tools.
          // settings={<ChatSettings containerRef={containerRef} />}
          formRef={formRef}
          inputProps={{
            placeholder: 'Ask a question…',
            ...register('input', { required: true }),
          }}
        >
          {!isPending ? (
            <Button
              type="submit"
              renderIcon={Send}
              kind="ghost"
              size="sm"
              hasIconOnly
              iconDescription={isFileUploadPending ? 'Files are uploading' : 'Send'}
              disabled={isSubmitDisabled}
            />
          ) : (
            <Button
              renderIcon={StopOutlineFilled}
              kind="ghost"
              size="sm"
              hasIconOnly
              iconDescription="Cancel"
              onClick={(e) => {
                cancel();
                e.preventDefault();
              }}
            />
          )}
        </InputBar>
      </div>
    </FormProvider>
  );
});

export interface ChatFormValues {
  input: string;
  tools?: string[];
}
