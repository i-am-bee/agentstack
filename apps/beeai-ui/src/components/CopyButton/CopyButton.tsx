/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Checkmark, Copy } from '@carbon/icons-react';
import { IconButton, type IconButtonProps } from '@carbon/react';
import { type RefObject, useCallback, useState } from 'react';

interface Props {
  contentRef: RefObject<HTMLElement | null>;
  size?: IconButtonProps['size'];
}

export function CopyButton({ contentRef, size = 'md' }: Props) {
  const [copied, setCopied] = useState(false);

  const handleClick = useCallback(() => {
    const text = contentRef.current?.innerText.trim();

    if (!text) {
      return;
    }

    navigator.clipboard.writeText(text);

    setCopied(true);

    setTimeout(() => {
      setCopied(false);
    }, COPIED_RESET_TIMEOUT);
  }, [contentRef]);

  return (
    <IconButton label="Copy" kind="ghost" size={size} onClick={handleClick} disabled={copied}>
      {copied ? <Checkmark /> : <Copy />}
    </IconButton>
  );
}

const COPIED_RESET_TIMEOUT = 2000;
