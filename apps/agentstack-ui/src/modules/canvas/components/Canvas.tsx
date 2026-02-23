/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { useEffect, useMemo, useRef } from 'react';

import { CopyButton } from '#components/CopyButton/CopyButton.tsx';
import { UIMessagePartKind } from '#modules/messages/types.ts';
import { applyTransforms } from '#modules/messages/utils.ts';
import { useSources } from '#modules/sources/contexts/index.ts';

import { useCanvas } from '../contexts';
import { CanvasMarkdownContent } from '../markdown/CanvasMarkdownContent';
import classes from './Canvas.module.scss';

export function Canvas() {
  const { activeArtifact } = useCanvas();
  const { activeSource, setActiveSource } = useSources();
  const contentRef = useRef(null);

  const content = useMemo(() => {
    if (!activeArtifact) return undefined;

    const rawContent = activeArtifact.parts
      .map((part) => (part.kind === UIMessagePartKind.Text ? part.text : ''))
      .join('');

    return applyTransforms(activeArtifact.parts, rawContent);
  }, [activeArtifact]);

  const sources = useMemo(
    () => activeArtifact?.parts.filter((part) => part.kind === UIMessagePartKind.Source) ?? [],
    [activeArtifact],
  );

  const isCode = useMemo(() => {
    const containsCodeBlockRegex = /.+```.+/;
    return Boolean(content && content.startsWith('```') && !containsCodeBlockRegex.test(content));
  }, [content]);

  useEffect(() => {
    return () => {
      if (activeSource?.artifactId === activeArtifact?.artifactId) {
        setActiveSource(null);
      }
    };
  }, [activeArtifact, activeSource, setActiveSource]);

  if (!activeArtifact) {
    return null;
  }

  return (
    <div className={clsx(classes.root, { [classes.codeBlock]: isCode })}>
      <div className={classes.container}>
        {!isCode && (
          <header className={classes.header}>
            {activeArtifact.name && <h2 className={classes.heading}>{activeArtifact.name}</h2>}

            <div className={classes.actions}>
              <CopyButton contentRef={contentRef} />
            </div>
          </header>
        )}

        <div ref={contentRef}>
          <CanvasMarkdownContent className={classes.content} artifactId={activeArtifact.artifactId} sources={sources}>
            {content}
          </CanvasMarkdownContent>
        </div>
      </div>
    </div>
  );
}
