/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useRef } from 'react';

import { CopyButton } from '#components/CopyButton/CopyButton.tsx';
import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import { UIMessagePartKind } from '#modules/messages/types.ts';

import { useCanvas } from '../contexts';
import classes from './Canvas.module.scss';

export function Canvas() {
  const { activeArtifact } = useCanvas();
  const contentRef = useRef(null);

  if (!activeArtifact) {
    return null;
  }

  return (
    <div className={classes.root}>
      <div className={classes.container}>
        <header className={classes.header}>
          {activeArtifact.name && <h2 className={classes.heading}>{activeArtifact.name}</h2>}

          <div className={classes.actions}>
            <CopyButton contentRef={contentRef} />
          </div>
        </header>

        <div className={classes.body} ref={contentRef}>
          {/* <Toolbar isVisible /> */}

          <MarkdownContent className={classes.content}>
            {activeArtifact?.parts.map((part) => part.kind === UIMessagePartKind.Text && part.text).join('')}
          </MarkdownContent>
        </div>
      </div>
    </div>
  );
}
