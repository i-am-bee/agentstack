/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import clsx from 'clsx';
import { type HTMLAttributes, useRef } from 'react';

import { CopyButton } from '#components/CopyButton/CopyButton.tsx';
import { LineClampText } from '#components/LineClampText/LineClampText.tsx';

import classes from './CodeSnippet.module.scss';

interface Props extends HTMLAttributes<HTMLElement> {
  forceExpand?: boolean;
  canCopy?: boolean;
  withBorder?: boolean;
}

export function CodeSnippet({ forceExpand, canCopy, withBorder, ...props }: Props) {
  const ref = useRef<HTMLElement>(null);

  const code = (
    <pre>
      <code ref={ref} {...props} />
    </pre>
  );

  return (
    <div className={clsx(classes.root, { [classes.withBorder]: withBorder })}>
      {canCopy && (
        <div className={classes.copyButton}>
          <CopyButton contentRef={ref} size="sm" align="bottom" />
        </div>
      )}

      <div className={classes.content}>{forceExpand ? code : <LineClampText lines={5}>{code}</LineClampText>}</div>
    </div>
  );
}
