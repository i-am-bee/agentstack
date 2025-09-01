/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback, useRef, useState } from 'react';
import { FormProvider, useForm } from 'react-hook-form';
import { mergeRefs } from 'react-merge-refs';

import { TextAreaAutoHeight } from '#components/TextAreaAutoHeight/TextAreaAutoHeight.tsx';
import { InteractionMode } from '#modules/agents/api/types.ts';
import { FileUploadButton } from '#modules/files/components/FileUploadButton.tsx';
import { useFileUpload } from '#modules/files/contexts/index.ts';
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';
import { dispatchInputEventOnTextarea, submitFormOnEnter } from '#utils/form-utils.ts';

import { ChatDefaultTools } from '../chat/constants';
import { useAgentRun } from '../contexts/agent-run';
import type { RunAgentFormValues } from '../types';
import { PromptExamples } from './PromptExamples';
import { RunFiles } from './RunFiles';
import classes from './RunInput.module.scss';
// import { RunSettings } from './RunSettings';
import { RunSubmit } from './RunSubmit';

interface Props {
  promptExamples?: string[];
  onSubmit?: () => void;
}

export function RunInput({ promptExamples, onSubmit }: Props) {
  const formRef = useRef<HTMLFormElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const [promptExamplesOpen, setPromptExamplesOpen] = useState(false);

  const { contextId, matchedProviders, selectProvider } = usePlatformContext();

  const {
    agent: {
      ui: { interaction_mode },
    },
    isPending,
    run,
    cancel,
  } = useAgentRun();
  const { isPending: isFileUploadPending, isDisabled: isFileUploadDisabled } = useFileUpload();

  const isChatUi = interaction_mode === InteractionMode.MultiTurn;

  const form = useForm<RunAgentFormValues>({
    mode: 'onChange',
    defaultValues: {
      tools: isChatUi ? ChatDefaultTools : [],
    },
  });

  const { watch, handleSubmit, register, setValue } = form;

  const inputProps = register('input', { required: true });
  const inputValue = watch('input');
  const isSubmitDisabled = isPending || isFileUploadPending || !inputValue || !contextId;

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
            onSubmit?.();
            resetForm();

            await run(input);
          })();
        }}
      >
        <RunFiles />
        {Object.entries(matchedProviders || {}).map(([key, value]) => (
          <div key={key}>
            <p>{key}</p>
            <select key={key} onChange={({ target }) => selectProvider(key, target.value)}>
              {value.map((provider) => (
                <option key={provider} value={provider}>
                  {provider}
                </option>
              ))}
            </select>
          </div>
        ))}

        <TextAreaAutoHeight
          rows={1}
          autoFocus
          placeholder="Ask anything…"
          className={classes.textarea}
          onKeyDown={(event) => !isSubmitDisabled && submitFormOnEnter(event)}
          {...inputProps}
          ref={mergeRefs([inputRef, inputProps.ref])}
        />

        <div className={classes.actionBar}>
          <div className={classes.actionBarStart}>
            {/* TODO: The API does not yet support tools. */}
            {/* <RunSettings containerRef={formRef} /> */}

            {!isFileUploadDisabled && <FileUploadButton />}
          </div>

          <div className={classes.submit}>
            <RunSubmit
              isPending={isPending}
              isFileUploadPending={isFileUploadPending}
              disabled={isSubmitDisabled}
              onCancel={cancel}
            />
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
