/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback, useRef, useState } from 'react';
import { FormProvider, useForm } from 'react-hook-form';
import { mergeRefs } from 'react-merge-refs';

import { TextAreaAutoHeight } from '#components/TextAreaAutoHeight/TextAreaAutoHeight.tsx';
import { SupportedUIType } from '#modules/agents/api/types.ts';
import { FileUploadButton } from '#modules/files/components/FileUploadButton.tsx';
import { useFileUpload } from '#modules/files/contexts/index.ts';
import { dispatchInputEventOnTextarea, submitFormOnEnter } from '#utils/form-utils.ts';

import { ChatDefaultTools } from '../chat/constants';
import { useAgentRun } from '../contexts/agent-run';
import type { RunAgentFormValues } from '../types';
import { PromptSuggestions } from './PromptSuggestions';
import { RunFiles } from './RunFiles';
import classes from './RunInput.module.scss';
// import { RunSettings } from './RunSettings';
import { RunSubmit } from './RunSubmit';

interface Props {
  promptSuggestions?: string[];
  onSubmit?: () => void;
}

export function RunInput({ promptSuggestions, onSubmit }: Props) {
  const formRef = useRef<HTMLFormElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const [promptSuggestionsOpen, setPromptSuggestionsOpen] = useState(false);

  const {
    agent: {
      ui: { ui_type: uiType },
    },
    isPending,
    run,
    cancel,
  } = useAgentRun();
  const { isPending: isFileUploadPending, isDisabled: isFileUploadDisabled } = useFileUpload();

  const isChatUi = uiType === SupportedUIType.Chat;

  const form = useForm<RunAgentFormValues>({
    mode: 'onChange',
    defaultValues: {
      tools: isChatUi ? ChatDefaultTools : [],
    },
  });

  const { watch, handleSubmit, register, setValue } = form;

  const inputProps = register('input', { required: true });
  const inputValue = watch('input');
  const isSubmitDisabled = isPending || isFileUploadPending || !inputValue;

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
      setPromptSuggestionsOpen(false);
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

        {promptSuggestions && (
          <PromptSuggestions
            inputRef={inputRef}
            suggestions={promptSuggestions}
            isOpen={promptSuggestionsOpen}
            setIsOpen={setPromptSuggestionsOpen}
            onSubmit={fillWithInput}
          />
        )}
      </form>
    </FormProvider>
  );
}
