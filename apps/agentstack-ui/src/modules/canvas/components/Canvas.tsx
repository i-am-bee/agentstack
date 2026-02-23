/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { useEffect, useMemo, useRef } from 'react';

import { CopyButton } from '#components/CopyButton/CopyButton.tsx';
import { UIMessagePartKind } from '#modules/messages/types.ts';
import { applyTransforms } from '#modules/messages/utils.ts';
import { SourcesGroup } from '#modules/sources/components/SourcesGroup.tsx';
import { useSources } from '#modules/sources/contexts/index.ts';

import { useCanvas } from '../contexts';
import { CanvasMarkdownContent } from '../markdown/CanvasMarkdownContent';
import classes from './Canvas.module.scss';

export function Canvas() {
  const { activeArtifact } = useCanvas();
  const contentRef = useRef(null);
  const { setActiveSource, activeSource } = useSources();

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
    const activeSourceArtifactId = activeSource?.artifactId;
    const artifactId = activeArtifact?.artifactId;
    const taskId = activeArtifact?.taskId;
    if (!artifactId || !taskId || !activeSourceArtifactId || activeSourceArtifactId === artifactId) {
      return;
    }

    setActiveSource({ number: null, taskId, artifactId });
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

        <SourcesGroup sources={sources} taskId={activeArtifact.taskId} artifactId={activeArtifact.artifactId} />
      </div>
    </div>
  );
}
