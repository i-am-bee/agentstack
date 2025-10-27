/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
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

  if (!parsed) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div {...fadeProps()} className={clsx(classes.root)}>
        {title && <h3 className={classes.name}>{title}</h3>}

        <div className={classes.body}>
          {match(parsed)
            .with({ type: 'string' }, ({ value }) => <LineClampText lines={5}>{value}</LineClampText>)
            .otherwise(({ value }) => {
              // if (hasDescription) {
              //   return <LineClampText lines={5}>{parsed.input.thought}</LineClampText>;
              // }
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
