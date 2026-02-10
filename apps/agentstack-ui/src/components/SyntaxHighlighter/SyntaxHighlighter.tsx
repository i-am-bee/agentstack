/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { CodeSnippetSkeleton } from '@carbon/react';
import clsx from 'clsx';
import dynamic from 'next/dynamic';

import { registerLanguagesAsync } from './languages';
import classes from './SyntaxHighlighter.module.scss';
import { blogStyle, customStyle, style } from './theme';

interface Props {
  language: string;
  children: string;
  className?: string;
  variant?: 'blog';
}

const Highlighter = dynamic(
  () =>
    import('react-syntax-highlighter').then(({ Light }) => {
      registerLanguagesAsync(Light);
      // Type assertion needed due to React 18/19 contextType incompatibility in react-syntax-highlighter types
      return Light as React.ComponentType<React.ComponentProps<typeof Light>>;
    }),
  {
    ssr: false,
    loading: () => <CodeSnippetSkeleton type="multi" className="" />,
  },
);

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
