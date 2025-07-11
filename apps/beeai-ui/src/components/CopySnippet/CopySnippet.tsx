/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import clsx from 'clsx';
import { type ReactElement, useRef } from 'react';

import { CopyButton } from '#components/CopyButton/CopyButton.tsx';

import classes from './CopySnippet.module.scss';

interface Props {
  children: string | ReactElement;
  className?: string;
}

export function CopySnippet({ children: snippet, className }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  return (
    <div className={clsx(classes.root, { [classes.block]: typeof snippet !== 'string' }, className)}>
      <div ref={ref} className={classes.content}>
        {typeof snippet === 'string' ? <code>{snippet}</code> : snippet}
      </div>

      <div className={classes.button}>
        <CopyButton contentRef={ref} />
      </div>
    </div>
  );
}
