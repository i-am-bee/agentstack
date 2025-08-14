/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CodeSnippet } from '#components/CodeSnippet/CodeSnippet.tsx';
import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { parseJsonLikeString } from '#modules/runs/utils.ts';

import classes from './TrajectoryItemContent.module.scss';

interface Props {
  trajectory: UITrajectoryPart;
}

export function TrajectoryItemContent({ trajectory }: Props) {
  const { content } = trajectory;

  if (!content) {
    return null;
  }

  const parsed = parseJsonLikeString(content);

  return (
    <div className={classes.root}>
      <div className={classes.group}>
        <div className={classes.content}>
          <CodeSnippet canCopy withBorder>
            {parsed}
          </CodeSnippet>
        </div>
      </div>
    </div>
  );
}
