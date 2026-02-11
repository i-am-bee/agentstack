/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { motion } from 'framer-motion';
import { useMemo } from 'react';
import { match } from 'ts-pattern';
import { v5 as uuidv5 } from 'uuid';

import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { maybeParseJson } from '#modules/runs/utils.ts';
import { fadeProps } from '#utils/fadeProps.ts';

import { CHARS_DELAY_MAX_MS } from '../hooks/useAnimatedText.ts';
import { AnimatedCodeContent } from './AnimatedCodeContent.tsx';
import { AnimatedTextContent } from './AnimatedTextContent.tsx';
import classes from './TrajectoryItem.module.scss';

interface Props {
  trajectory: UITrajectoryPart;
  isPending?: boolean;
  canClampContent?: boolean;
}

export function TrajectoryItem({ trajectory, isPending, canClampContent }: Props) {
  const { title, content, createdAt } = trajectory;

  const parsed = useMemo(() => maybeParseJson(content), [content]);

  const contentKey = useMemo(() => (content ? uuidv5(content, TRAJECTORY_NAMESPACE) : undefined), [content]);

  if (!parsed) {
    return null;
  }

  const shouldAnimateText = isPending && createdAt ? Date.now() - createdAt < SHOULD_ANIMATE_THRESHOLD_MS : false;
  const contentAnimationDelay = Math.min(CHARS_DELAY_MAX_MS * (title?.length ?? 0), TEXT_ANIMATION_DURATION_MS);

  return (
    <div className={clsx(classes.root, { [classes.isAnimating]: shouldAnimateText })}>
      {title && (
        <motion.h3 {...fadeProps()} className={classes.title} key={title}>
          <AnimatedTextContent shouldAnimate={shouldAnimateText} totalDurationMs={TEXT_ANIMATION_DURATION_MS}>
            {title}
          </AnimatedTextContent>
        </motion.h3>
      )}

      <motion.div {...fadeProps()} className={classes.body} key={contentKey}>
        {match(parsed)
          .with({ type: 'string' }, ({ value }) => (
            <AnimatedTextContent
              shouldAnimate={shouldAnimateText}
              totalDurationMs={TEXT_ANIMATION_DURATION_MS}
              delayMs={contentAnimationDelay}
              className={classes.content}
              linesClamp={!isPending && canClampContent ? 5 : undefined}
            >
              {value}
            </AnimatedTextContent>
          ))
          .otherwise(({ value }) => {
            return (
              <AnimatedCodeContent
                shouldAnimate={shouldAnimateText}
                totalDurationMs={TEXT_ANIMATION_DURATION_MS}
                delayMs={contentAnimationDelay}
              >
                {value}
              </AnimatedCodeContent>
            );
          })}
      </motion.div>
    </div>
  );
}

const TRAJECTORY_NAMESPACE = '1b671a64-40d5-431e-99b0-da01ff1f3341';
const TEXT_ANIMATION_DURATION_MS = 1500;
const SHOULD_ANIMATE_THRESHOLD_MS = 2 * TEXT_ANIMATION_DURATION_MS;
