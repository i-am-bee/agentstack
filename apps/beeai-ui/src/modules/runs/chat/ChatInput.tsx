/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
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

import { Send, StopOutlineFilled } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import { memo, useCallback, useRef } from 'react';
import { FormProvider, useForm } from 'react-hook-form';

import type { InputBarFormHandle } from '../components/InputBar';
import { InputBar } from '../components/InputBar';
import { useChat } from '../contexts/chat';
import { useFileUpload } from '../files/contexts';
// import { ChatSettings } from './ChatSettings';
import { ChatDefaultTools } from './constants';

interface Props {
  onMessageSubmit?: () => void;
}

export const ChatInput = memo(function ChatInput({ onMessageSubmit }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<InputBarFormHandle>(null);

  const { isPending, sendMessage, onCancel } = useChat();
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

              await sendMessage(input);
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
                onCancel();
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
