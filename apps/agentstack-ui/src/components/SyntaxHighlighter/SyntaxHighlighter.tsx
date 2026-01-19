'use client';
/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { CodeSnippetSkeleton } from '@carbon/react';
import dynamic from 'next/dynamic';

interface Props {
  language: string;
  children: string;
  className?: string;
  variant?: 'blog';
}

const SyntaxHighlighterDynamic = dynamic(() => import('./SyntaxHighlighterImpl'), {
  ssr: false,
  loading: () => <CodeSnippetSkeleton type="multi" className="" />,
});

export function SyntaxHighlighter({ language, className, variant, children }: Props) {
  return (
    <SyntaxHighlighterDynamic language={language} className={className} variant={variant}>
      {children}
    </SyntaxHighlighterDynamic>
  );
}
