/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { motion } from 'framer-motion';
import { useMemo } from 'react';
import { match } from 'ts-pattern';
import { v5 as uuidv5 } from 'uuid';

import { CodeSnippet } from '#components/CodeSnippet/CodeSnippet.tsx';
import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { maybeParseJson } from '#modules/runs/utils.ts';
import { fadeProps } from '#utils/fadeProps.ts';

import { AnimatedText } from './AnimatedText.tsx';
import classes from './TrajectoryItem.module.scss';

interface Props {
  trajectory: UITrajectoryPart;
  isPending?: boolean;
}

export function TrajectoryItem({ trajectory, isPending }: Props) {
  const { title, content, createdAt } = trajectory;

  const parsed = useMemo(() => maybeParseJson(content), [content]);

  const contentKey = useMemo(() => (content ? uuidv5(content, TRAJECTORY_NAMESPACE) : undefined), [content]);

  if (!parsed) {
    return null;
  }

  const shouldAnimateText = isPending && createdAt ? Date.now() - createdAt < TEXT_ANIMATION_DURATION_MS : false;

  return (
    <div className={clsx(classes.root, { [classes.isAnimating]: shouldAnimateText })}>
      {title && (
        <motion.h3 {...fadeProps()} className={classes.title} key={title}>
          <AnimatedText shouldAnimate={shouldAnimateText}>{title}</AnimatedText>
        </motion.h3>
      )}

      <motion.div {...fadeProps()} className={classes.body} key={contentKey}>
        {match(parsed)
          .with({ type: 'string' }, ({ value }) => (
            <AnimatedText
              shouldAnimate={shouldAnimateText}
              className={classes.content}
              lineClamp={!isPending ? { lines: 5, useBlockElement: true } : undefined}
            >
              {value}
            </AnimatedText>
          ))
          .otherwise(({ value }) => {
            return (
              <CodeSnippet canCopy withBorder>
                {value}
              </CodeSnippet>
            );
          })}
      </motion.div>
    </div>
  );
}

const TRAJECTORY_NAMESPACE = '1b671a64-40d5-431e-99b0-da01ff1f3341';
const TEXT_ANIMATION_DURATION_MS = 1500;
