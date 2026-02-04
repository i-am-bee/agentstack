/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { motion } from 'framer-motion';
import { useMemo } from 'react';
import { match } from 'ts-pattern';
import Typewriter from 'typewriter-effect';
import { v5 as uuidv5 } from 'uuid';

import { CodeSnippet } from '#components/CodeSnippet/CodeSnippet.tsx';
import { LineClampText } from '#components/LineClampText/LineClampText.tsx';
import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { maybeParseJson } from '#modules/runs/utils.ts';
import { fadeProps } from '#utils/fadeProps.ts';

import { AnimatedMarkdown } from './AnimatedMarkdown.tsx';
import classes from './TrajectoryItem.module.scss';

interface Props {
  trajectory: UITrajectoryPart;
}

const TYPEWRITER_TOTAL_DURATION_MS = 1500;
const TYPEWRITER_MAX_DELAY_MS = 20;

export function TrajectoryItem({ trajectory }: Props) {
  const { title, content } = trajectory;

  const parsed = useMemo(() => maybeParseJson(content), [content]);

  const contentKey = useMemo(() => (content ? uuidv5(content, TRAJECTORY_NAMESPACE) : undefined), [content]);

  if (!parsed) {
    return null;
  }

  return (
    <div className={clsx(classes.root)}>
      {title && (
        <motion.h3 {...fadeProps()} className={classes.name} key={title}>
          <Typewriter
            options={{
              strings: title,
              autoStart: true,
              delay: Math.min(TYPEWRITER_TOTAL_DURATION_MS / title.length, TYPEWRITER_MAX_DELAY_MS),
              cursor: '',
            }}
          />
        </motion.h3>
      )}

      <motion.div {...fadeProps()} className={classes.body} key={contentKey}>
        {match(parsed)
          .with({ type: 'string' }, ({ value }) => (
            <LineClampText lines={5} useBlockElement>
              <AnimatedMarkdown className={classes.content}>{value}</AnimatedMarkdown>
            </LineClampText>
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
