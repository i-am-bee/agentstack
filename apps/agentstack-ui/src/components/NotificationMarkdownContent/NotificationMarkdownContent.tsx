/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { useMemo } from 'react';
import type { Components } from 'react-markdown';

import { LineClampText } from '#components/LineClampText/LineClampText.tsx';
import { Code } from '#components/MarkdownContent/components/Code.tsx';
import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';

import classes from './NotificationMarkdownContent.module.scss';

interface Props {
  children: string;
}

export function NotificationMarkdownContent({ children }: Props) {
  const components: Components = useMemo(
    () => ({
      code: ({ className, ...props }) => <Code {...props} className={clsx(className, classes.code)} />,
    }),
    [],
  );

  return (
    <LineClampText className={classes.root} lines={4} useBlockElement autoExpandOnContentChange>
      <MarkdownContent className={classes.markdown} components={components}>
        {children}
      </MarkdownContent>
    </LineClampText>
  );
}
