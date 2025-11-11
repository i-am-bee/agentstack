/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { motion } from 'framer-motion';
import { useMemo } from 'react';
import { match } from 'ts-pattern';

import { CodeSnippet } from '#components/CodeSnippet/CodeSnippet.tsx';
import { LineClampText } from '#components/LineClampText/LineClampText.tsx';
import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { maybeParseJson } from '#modules/runs/utils.ts';
import { fadeProps } from '#utils/fadeProps.ts';
import { isNotNull } from '#utils/helpers.ts';

import classes from './TrajectoryItem.module.scss';

interface Props {
  trajectory: UITrajectoryPart;
}

export function TrajectoryItem({ trajectory }: Props) {
  const { title, content } = trajectory;

  const parsed = useMemo(() => content?.map(maybeParseJson).filter(isNotNull), [content]);

  if (!parsed) {
    return null;
  }

  return (
    <motion.div {...fadeProps()} className={clsx(classes.root)}>
      {title && <h3 className={classes.name}>{title}</h3>}

      <div className={classes.body}>
        {parsed.map((item, idx) =>
          match(item)
            .with({ type: 'string' }, ({ value }) => (
              <LineClampText lines={5} key={idx}>
                {value}
              </LineClampText>
            ))
            .otherwise(({ value }) => {
              return (
                <CodeSnippet canCopy withBorder key={idx}>
                  {value}
                </CodeSnippet>
              );
            }),
        )}
      </div>
    </motion.div>
  );
}
