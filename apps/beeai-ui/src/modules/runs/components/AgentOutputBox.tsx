/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CopyButton } from '@carbon/react';

import { DownloadButton } from '#components/DownloadButton/DownloadButton.tsx';
import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';

import classes from './AgentOutputBox.module.scss';

interface Props {
  isPending: boolean;
  text?: string;
  downloadFileName?: string;
}

export function AgentOutputBox({ isPending, text, downloadFileName }: Props) {
  return text ? (
    <div className={classes.root}>
      {!isPending && (
        <div className={classes.actions}>
          <CopyButton kind="ghost" align="left" onClick={() => navigator.clipboard.writeText(text)} />

          <DownloadButton filename={`${downloadFileName ?? 'output'}.txt`} content={text} />
        </div>
      )}

      <MarkdownContent>{text}</MarkdownContent>
    </div>
  ) : null;
}
