/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FormEventHandler, PropsWithChildren, ReactNode, Ref, TextareaHTMLAttributes } from 'react';
import { useImperativeHandle, useRef } from 'react';

import { TextAreaAutoHeight } from '#components/TextAreaAutoHeight/TextAreaAutoHeight.tsx';
import { useFileUpload } from '#modules/files/contexts/index.ts';
import { dispatchInputEventOnFormTextarea, submitFormOnEnter } from '#utils/form-utils.ts';

import { FileCard } from '../../files/components/FileCard';
import { FileCardsList } from '../../files/components/FileCardsList';
import { FileUploadButton } from '../../files/components/FileUploadButton';
import { AgentModel } from './AgentModel';
import classes from './InputBar.module.scss';

interface Props {
  isSubmitDisabled?: boolean;
  settings?: ReactNode;
  formRef?: Ref<InputBarFormHandle>;
  inputProps?: TextareaHTMLAttributes<HTMLTextAreaElement>;
  onSubmit?: FormEventHandler;
}

export type InputBarFormHandle = {
  resetForm: () => void;
};

export function InputBar({
  isSubmitDisabled,
  settings,
  formRef: formRefProp,
  inputProps,
  onSubmit,
  children,
}: PropsWithChildren<Props>) {
  const formRef = useRef<HTMLFormElement>(null);
  const { files, removeFile, isDisabled: isFileUploadDisabled } = useFileUpload();

  useImperativeHandle(
    formRefProp,
    () => ({
      resetForm() {
        const formElem = formRef.current;
        if (!formElem) return;

        formElem.reset();

        dispatchInputEventOnFormTextarea(formElem);
      },
    }),
    [],
  );

  return (
    <form
      className={classes.root}
      ref={formRef}
      onSubmit={(event) => {
        event.preventDefault();

        if (isSubmitDisabled) return;

        onSubmit?.(event);
      }}
    >
      {files.length > 0 && (
        <div className={classes.files}>
          <FileCardsList>
            {files.map(({ id, originalFile: { name }, status }) => (
              <li key={id}>
                <FileCard size="sm" filename={name} status={status} onRemoveClick={() => removeFile(id)} />
              </li>
            ))}
          </FileCardsList>
        </div>
      )}

      <TextAreaAutoHeight
        rows={1}
        autoFocus
        {...inputProps}
        className={classes.textarea}
        onKeyDown={(event) => !isSubmitDisabled && submitFormOnEnter(event)}
      />
      <div className={classes.actionBar}>
        <div className={classes.actionBarStart}>
          {settings && <div className={classes.settings}>{settings}</div>}

          {!isFileUploadDisabled && <FileUploadButton />}

          <AgentModel />
        </div>

        <div className={classes.submit}>{children}</div>
      </div>
    </form>
  );
}
