/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CopyButton } from '@carbon/react';
import type { PropsWithChildren } from 'react';

import { DownloadButton } from '#components/DownloadButton/DownloadButton.tsx';
import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';

import type { SourceReference } from '../sources/api/types';
import classes from './AgentOutputBox.module.scss';

interface Props {
  isPending: boolean;
  text?: string;
  downloadFileName?: string;
  sources?: SourceReference[];
}

export function AgentOutputBox({ isPending, text, downloadFileName, sources, children }: PropsWithChildren<Props>) {
  return text || children ? (
    <div className={classes.root}>
      {!isPending && text && (
        <div className={classes.actions}>
          <CopyButton kind="ghost" align="left" onClick={() => navigator.clipboard.writeText(text)} />

          <DownloadButton filename={`${downloadFileName ?? 'output'}.txt`} content={text} />
        </div>
      )}

      {text && <MarkdownContent sources={sources}>{text}</MarkdownContent>}

      {children && <div>{children}</div>}
    </div>
  ) : null;
}
