/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { InlineLoading } from '@carbon/react';
import { useCallback, useRef, useState } from 'react';
import { FormProvider, useForm } from 'react-hook-form';
import { mergeRefs } from 'react-merge-refs';

import { TextAreaAutoHeight } from '#components/TextAreaAutoHeight/TextAreaAutoHeight.tsx';
import { useApp } from '#contexts/App/index.ts';
import { InteractionMode } from '#modules/agents/api/types.ts';
import { FileUploadButton } from '#modules/files/components/FileUploadButton.tsx';
import { useFileUpload } from '#modules/files/contexts/index.ts';
import { dispatchInputEventOnTextarea, submitFormOnEnter } from '#utils/form-utils.ts';

import { ChatDefaultTools } from '../chat/constants';
import { useAgentRun } from '../contexts/agent-run';
import { RunSettings } from '../settings/RunSettings';
import type { RunRunFormValues } from '../types';
import { MCPConfig } from './MCPConfig';
import { PromptExamples } from './PromptExamples';
import { RunFiles } from './RunFiles';
import classes from './RunInput.module.scss';
// import { RunSettings } from './RunSettings';
import { RunSubmit } from './RunSubmit';
import { OpenRouterModelProviders } from './OpenRouterModelProviders';

interface Props {
  promptExamples?: string[];
}

export function RunInput({ promptExamples }: Props) {
  const formRef = useRef<HTMLFormElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const [promptExamplesOpen, setPromptExamplesOpen] = useState(false);

  const { featureFlags } = useApp();

  const {
    agent: {
      ui: { interaction_mode },
    },
    isReady,
    isPending,
    isInitializing,
    chat,
    cancel,
  } = useAgentRun();
  const { isPending: isFileUploadPending, isDisabled: isFileUploadDisabled } = useFileUpload();

  const isChatUi = interaction_mode === InteractionMode.MultiTurn;

  const form = useForm<RunRunFormValues>({
    mode: 'onChange',
    defaultValues: {
      tools: isChatUi ? ChatDefaultTools : [],
    },
  });

  const { watch, handleSubmit, register, setValue } = form;

  const inputProps = register('input', { required: true });
  const inputValue = watch('input');
  const isSubmitDisabled = !isReady || isFileUploadPending || !inputValue;

  const dispatchInputEventAndFocus = useCallback(() => {
    const inputElem = inputRef.current;

    if (!inputElem) {
      return;
    }

    inputElem.focus();
    dispatchInputEventOnTextarea(inputElem);
  }, []);

  const resetForm = useCallback(() => {
    const formElem = formRef.current;

    formElem?.reset();
    dispatchInputEventAndFocus();
  }, [dispatchInputEventAndFocus]);

  const fillWithInput = useCallback(
    (value: string) => {
      setValue('input', value, { shouldValidate: true });
      setPromptExamplesOpen(false);
      dispatchInputEventAndFocus();
    },
    [setValue, dispatchInputEventAndFocus],
  );

  return (
    <FormProvider {...form}>
      <form
        className={classes.root}
        ref={formRef}
        onSubmit={(event) => {
          event.preventDefault();

          if (isSubmitDisabled) {
            return;
          }

          handleSubmit(async ({ input }) => {
            resetForm();

            await chat(input);
          })();
        }}
      >
        <RunFiles />

        <TextAreaAutoHeight
          rows={1}
          maxRows={7}
          autoFocus
          placeholder="Ask anything…"
          className={classes.textarea}
          onKeyDown={(event) => !isSubmitDisabled && submitFormOnEnter(event)}
          {...inputProps}
          ref={mergeRefs([inputRef, inputProps.ref])}
        />

        <div className={classes.actionBar}>
          <div className={classes.actionBarStart}>
            <RunSettings containerRef={formRef} />

            {!isFileUploadDisabled && <FileUploadButton />}

            {featureFlags.MCP && <MCPConfig />}

            {/* {featureFlags.ModelProviders && <ModelProviders />} */}
            <OpenRouterModelProviders />
          </div>

          <div className={classes.submit}>
            {!isInitializing ? (
              <RunSubmit
                isPending={isPending}
                isFileUploadPending={isFileUploadPending}
                disabled={isSubmitDisabled}
                onCancel={cancel}
              />
            ) : (
              <InlineLoading iconDescription="Initializing conversation" />
            )}
          </div>
        </div>

        {promptExamples && (
          <PromptExamples
            inputRef={inputRef}
            examples={promptExamples}
            isOpen={promptExamplesOpen}
            setIsOpen={setPromptExamplesOpen}
            onSubmit={fillWithInput}
          />
        )}
      </form>
    </FormProvider>
  );
}
