/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import has from 'lodash/has';
import { useMemo } from 'react';
import { match } from 'ts-pattern';

import { CodeSnippet } from '#components/CodeSnippet/CodeSnippet.tsx';
import { LineClampText } from '#components/LineClampText/LineClampText.tsx';
import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { maybeParseJson } from '#modules/runs/utils.ts';
import { fadeProps } from '#utils/fadeProps.ts';

import classes from './TrajectoryItem.module.scss';

interface Props {
  trajectory: UITrajectoryPart;
}

export function TrajectoryItem({ trajectory }: Props) {
  const { title, content } = trajectory;

  const parsed = useMemo(() => maybeParseJson(content), [content]);

  const name = useMemo(() => {
    if (isThoughtTrajectory(parsed?.parsed)) {
      return 'Thought';
    }

    return title;
  }, [parsed, title]);

  if (!parsed) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div {...fadeProps()} className={clsx(classes.root)}>
        {name && <h3 className={classes.name}>{name}</h3>}

        <div className={classes.body}>
          {match(parsed)
            .with({ type: 'string' }, ({ value }) => <LineClampText lines={5}>{value}</LineClampText>)
            .otherwise(({ value, parsed }) => {
              if (isThoughtTrajectory(parsed)) {
                return <LineClampText lines={5}>{parsed.input.thought}</LineClampText>;
              }
              return (
                <CodeSnippet canCopy withBorder>
                  {value}
                </CodeSnippet>
              );
            })}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

interface ThoughtTrajectory {
  input: {
    thought: string;
  };
}

function isThoughtTrajectory(trajectory: unknown): trajectory is ThoughtTrajectory {
  return has(trajectory, 'input.thought');
}
