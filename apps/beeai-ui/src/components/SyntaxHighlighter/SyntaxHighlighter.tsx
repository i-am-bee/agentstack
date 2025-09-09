/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { Light as Highlighter } from 'react-syntax-highlighter';

import { registerLanguages } from './languages';
import classes from './SyntaxHighlighter.module.scss';
import { blogStyle, customStyle, style } from './theme';

interface Props {
  language: string;
  children: string;
  className?: string;
  variant?: 'blog';
}

export function SyntaxHighlighter({ language, className, variant, children }: Props) {
  const isBlogVariant = variant === 'blog';

  return (
    <div className={clsx(classes.container, className, { [classes.blog]: isBlogVariant })}>
      <Highlighter
        style={style}
        customStyle={isBlogVariant ? blogStyle : customStyle}
        language={language}
        wrapLongLines
      >
        {children}
      </Highlighter>
    </div>
  );
}

registerLanguages(Highlighter);
