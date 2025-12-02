/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CopyButton } from '@carbon/react';
import type { PropsWithChildren } from 'react';

import { DownloadButton } from '#components/DownloadButton/DownloadButton.tsx';
import type { UISourcePart } from '#modules/messages/types.ts';

import { ChatMarkdownContent } from './ChatMarkdownContent/ChatMarkdownContent';
import classes from './RunOutputBox.module.scss';

interface Props {
  isPending: boolean;
  text?: string;
  downloadFileName?: string;
  sources?: UISourcePart[];
}

export function RunOutputBox({ isPending, text, downloadFileName, sources, children }: PropsWithChildren<Props>) {
  return text || children ? (
    <div className={classes.root}>
      {!isPending && text && (
        <div className={classes.actions}>
          <CopyButton kind="ghost" align="left" onClick={() => navigator.clipboard.writeText(text)} />

          <DownloadButton filename={`${downloadFileName ?? 'output'}.txt`} content={text} />
        </div>
      )}

      {text && (
        <ChatMarkdownContent sources={sources} codeBlocksExpanded={isPending} showMermaidDiagrams={!isPending}>
          {text}
        </ChatMarkdownContent>
      )}

      <div className={classes.holder}>{children}</div>
    </div>
  ) : null;
}
