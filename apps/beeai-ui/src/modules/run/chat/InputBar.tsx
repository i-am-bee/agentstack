/**
 * Copyright 2025 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { TextAreaAutoHeight } from '#components/TextAreaAutoHeight/TextAreaAutoHeight.tsx';
import { dispatchInputEventOnFormTextarea, submitFormOnEnter } from '#utils/formUtils.ts';
import { Send, StopOutlineFilled } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import { memo, useCallback, useRef } from 'react';
import { FormProvider, useForm } from 'react-hook-form';
import { mergeRefs } from 'react-merge-refs';
import { useChat } from '../contexts';
import { ChatSettings } from './ChatSettings';
import classes from './InputBar.module.scss';
import { ChatDefaultTools } from './constants';

interface Props {
  onMessageSubmit?: () => void;
}

export const InputBar = memo(function InputBar({ onMessageSubmit }: Props) {
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const formRef = useRef<HTMLFormElement>(null);

  const { sendMessage, onCancel } = useChat();

  const form = useForm<ChatFormValues>({
    mode: 'onChange',
    defaultValues: {
      tools: ChatDefaultTools,
    },
  });

  const {
    register,
    watch,
    handleSubmit,
    formState: { isSubmitting },
  } = form;

  const resetForm = useCallback(() => {
    {
      const formElem = formRef.current;
      if (!formElem) return;

      formElem.reset();

      dispatchInputEventOnFormTextarea(formElem);
    }
  }, []);

  // const handleAfterRemoveSentMessage = useCallback(
  //   (message: UserChatMessage) => {
  //     setValue('input', message.content, { shouldValidate: true });
  //   },
  //   [setValue],
  // );

  const isPending = isSubmitting; // status !== 'ready';
  const inputValue = watch('input');

  const { ref: inputFormRef, ...inputFormProps } = register('input', {
    required: true,
  });

  const isSubmitDisabled = isPending || !inputValue;

  const placeholder = 'Ask a question…';

  return (
    <FormProvider {...form}>
      <form
        className={classes.root}
        ref={formRef}
        onSubmit={(e) => {
          e.preventDefault();
          if (isSubmitDisabled) return;

          handleSubmit(async ({ input, tools }) => {
            onMessageSubmit?.();
            resetForm();

            await sendMessage({ input, config: { tools } });
          })();
        }}
      >
        <TextAreaAutoHeight
          className={classes.textarea}
          rows={1}
          placeholder={placeholder}
          autoFocus
          ref={mergeRefs([inputFormRef, inputRef])}
          {...inputFormProps}
          onKeyDown={(e) => !isSubmitDisabled && submitFormOnEnter(e)}
        />

        <div className={classes.actionBar}>
          <div className={classes.actions}>
            <ChatSettings containerRef={formRef} />
          </div>

          <div>
            {!isPending ? (
              <Button
                type="submit"
                renderIcon={Send}
                kind="ghost"
                size="sm"
                hasIconOnly
                iconDescription="Send"
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
                  onCancel();
                  e.preventDefault();
                }}
              />
            )}
          </div>
        </div>
      </form>
    </FormProvider>
  );
});

export interface ChatFormValues {
  input: string;
  tools?: string[];
}
