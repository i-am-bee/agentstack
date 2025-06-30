/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Checkmark, Copy } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import clsx from 'clsx';
import { type ReactElement, useRef, useState } from 'react';

import classes from './CopySnippet.module.scss';

interface Props {
  children: string | ReactElement;
  className?: string;
}

export function CopySnippet({ children: snippet, className }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false);

  const handleCopyClick = () => {
    const text = ref.current?.innerText.trim();
    if (!text) {
      return;
    }

    navigator.clipboard.writeText(text);

    setCopied(true);
    setTimeout(() => {
      setCopied(false);
    }, 2000);
  };

  return (
    <div className={clsx(classes.root, { [classes.block]: typeof snippet !== 'string' }, className)}>
      <div ref={ref} className={classes.content}>
        {typeof snippet === 'string' ? <code>{snippet}</code> : snippet}
      </div>

      <div className={classes.button}>
        <IconButton label="Copy" kind="ghost" size="md" onClick={handleCopyClick} disabled={copied}>
          {copied ? <Checkmark /> : <Copy />}
        </IconButton>
      </div>
    </div>
  );
}
