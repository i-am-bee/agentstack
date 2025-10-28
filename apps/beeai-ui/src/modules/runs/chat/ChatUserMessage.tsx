/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { useState } from 'react';

import { LineClampText } from '#components/LineClampText/LineClampText.tsx';
import { MessageFiles } from '#modules/files/components/MessageFiles.tsx';
import { MessageFormProvider } from '#modules/form/contexts/MessageFormProvider.tsx';
import { MessageContent } from '#modules/messages/components/MessageContent.tsx';
import type { UIUserMessage } from '#modules/messages/types.ts';

import classes from './ChatUserMessage.module.scss';

interface Props {
  message: UIUserMessage;
}

export function ChatUserMessage({ message }: Props) {
  const [showSubmission, setShowSubmission] = useState(false);

  const { form } = message;
  const hasFormWithResponse = Boolean(form?.response);

  return (
    <MessageFormProvider showSubmission={showSubmission} setShowSubmission={setShowSubmission}>
      <div className={classes.root}>
        <div className={clsx(classes.content, { [classes.limitWidth]: !showSubmission })}>
          {hasFormWithResponse ? (
            <MessageContent message={message} />
          ) : (
            <LineClampText lines={3} buttonClassName={classes.moreButton} iconButton useBlockElement>
              <MessageContent message={message} />
            </LineClampText>
          )}
        </div>

        <MessageFiles message={message} className={classes.files} />
      </div>
    </MessageFormProvider>
  );
}
