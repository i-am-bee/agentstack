/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { CodeSnippet } from '#components/CodeSnippet/CodeSnippet.tsx';
import { LineClampText } from '#components/LineClampText/LineClampText.tsx';
import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { maybeParseJson } from '#modules/runs/utils.ts';

import classes from './TrajectoryItemContent.module.scss';

interface Props {
  trajectory: UITrajectoryPart;
}

export function TrajectoryItemContent({ trajectory }: Props) {
  const { content } = trajectory;

  const parsed = useMemo(() => maybeParseJson(content), [content]);

  if (!parsed) {
    return null;
  }

  const { type, value } = parsed;

  return (
    <div className={classes.root}>
      <div className={classes.group}>
        <div className={classes.content}>
          {type === 'string' ? (
            <LineClampText lines={5}>{value}</LineClampText>
          ) : (
            <CodeSnippet canCopy withBorder>
              {value}
            </CodeSnippet>
          )}
        </div>
      </div>
    </div>
  );
}
