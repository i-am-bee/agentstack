/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type HTMLAttributes, useRef } from 'react';

import { CopyButton } from '#components/CopyButton/CopyButton.tsx';
import { LineClampText } from '#components/LineClampText/LineClampText.tsx';

import classes from './CodeSnippet.module.scss';

interface Props extends HTMLAttributes<HTMLElement> {
  forceExpand?: boolean;
  canCopy?: boolean;
}

export function CodeSnippet({ forceExpand, canCopy, ...props }: Props) {
  const ref = useRef<HTMLElement>(null);

  const code = <code ref={ref} {...props} />;

  return (
    <div className={classes.root}>
      {canCopy && (
        <div className={classes.copyButton}>
          <CopyButton contentRef={ref} size="sm" />
        </div>
      )}

      <div className={classes.content}>{forceExpand ? code : <LineClampText lines={5}>{code}</LineClampText>}</div>
    </div>
  );
}
