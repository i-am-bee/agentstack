/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Light as Highlighter } from 'react-syntax-highlighter';

import { registerLanguages } from './languages';
import classes from './SyntaxHighlighter.module.scss';
import { customStyle, style } from './theme';

interface Props {
  language: string;
  children: string;
}

export function SyntaxHighlighter({ language, children }: Props) {
  return (
    <div className={classes.container}>
      <Highlighter style={style} customStyle={customStyle} language={language} wrapLongLines>
        {children}
      </Highlighter>
    </div>
  );
}

registerLanguages(Highlighter);
