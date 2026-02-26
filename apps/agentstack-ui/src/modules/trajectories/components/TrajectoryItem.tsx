/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { motion } from 'framer-motion';
import { useEffect } from 'react';
import { match } from 'ts-pattern';
import { v5 as uuidv5 } from 'uuid';

import { maybeParseJson } from '#modules/runs/utils.ts';
import { fadeProps } from '#utils/fadeProps.ts';

import { AnimationStatus, CHARS_DELAY_MAX_MS, DEFAULT_MAX_ANIMATED_CHARS } from '../hooks/useAnimatedText.ts';
import { AnimatedCodeContent } from './AnimatedCodeContent.tsx';
import { AnimatedTextContent } from './AnimatedTextContent.tsx';
import classes from './TrajectoryItem.module.scss';
import type { AnimatedTrajectory } from './TrajectoryList.tsx';

interface Props {
  trajectory: AnimatedTrajectory;
  isPending?: boolean;
  canClampContent?: boolean;
  animateStatus: AnimationStatus;
  onAnimationEnd: () => void;
}

export function TrajectoryItem({ trajectory, isPending, canClampContent, animateStatus, onAnimationEnd }: Props) {
  const { title, content } = trajectory;

  const parsed = maybeParseJson(content);

  const contentKey = content ? uuidv5(content, TRAJECTORY_NAMESPACE) : undefined;

  const isAnimating = animateStatus === AnimationStatus.Animating;

  const titleLength = title?.length ?? 0;
  const contentCharsToAnimate = Math.min(parsed?.value.length ?? 0, DEFAULT_MAX_ANIMATED_CHARS);
  const totalCharsToAnimate = titleLength + contentCharsToAnimate;
  const delayPerChar =
    totalCharsToAnimate > 0 && trajectory.duration
      ? Math.min(trajectory.duration / totalCharsToAnimate, CHARS_DELAY_MAX_MS)
      : 0;

  const titleDuration = titleLength * delayPerChar;
  const contentDuration = contentCharsToAnimate * delayPerChar;

  const hasContent = Boolean(parsed);

  useEffect(() => {
    if (!hasContent && !title && isAnimating) {
      onAnimationEnd();
    }
  }, [hasContent, isAnimating, onAnimationEnd, title]);

  return (
    <div className={clsx(classes.root, { [classes.isAnimating]: isAnimating })}>
      {title && (
        <motion.h3
          {...fadeProps()}
          className={classes.title}
          key={title}
          onAnimationEnd={!hasContent ? onAnimationEnd : undefined}
        >
          <AnimatedTextContent status={animateStatus} totalDurationMs={titleDuration}>
            {title}
          </AnimatedTextContent>
        </motion.h3>
      )}

      {parsed && (
        <motion.div {...fadeProps()} className={classes.body} key={contentKey}>
          {match(parsed)
            .with({ type: 'string' }, ({ value }) => (
              <AnimatedTextContent
                status={animateStatus}
                totalDurationMs={contentDuration}
                delayMs={titleDuration}
                className={classes.content}
                linesClamp={!isPending && canClampContent ? 5 : undefined}
                maxAnimatedChars={DEFAULT_MAX_ANIMATED_CHARS}
                onAnimationEnd={onAnimationEnd}
              >
                {value}
              </AnimatedTextContent>
            ))
            .otherwise(({ value }) => {
              return (
                <AnimatedCodeContent
                  status={animateStatus}
                  totalDurationMs={contentDuration}
                  delayMs={titleDuration}
                  maxAnimatedChars={DEFAULT_MAX_ANIMATED_CHARS}
                  onAnimationEnd={onAnimationEnd}
                >
                  {value}
                </AnimatedCodeContent>
              );
            })}
        </motion.div>
      )}
    </div>
  );
}

const TRAJECTORY_NAMESPACE = '1b671a64-40d5-431e-99b0-da01ff1f3341';
