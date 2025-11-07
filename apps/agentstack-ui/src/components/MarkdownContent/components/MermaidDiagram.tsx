/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import mermaid from 'mermaid';
import { type HTMLAttributes, useEffect, useId, useState } from 'react';
import type { ExtraProps } from 'react-markdown';

import { useTheme } from '#contexts/Theme/index.ts';
import { Theme } from '#contexts/Theme/types.ts';

import { Code } from './Code';
import classes from './MermaidDiagram.module.scss';

export type MermaidDiagramProps = HTMLAttributes<HTMLElement> & ExtraProps;

export function MermaidDiagram({ children }: MermaidDiagramProps) {
  const id = useId();
  const [diagram, setDiagram] = useState<string | null>(null);

  const { theme } = useTheme();

  useEffect(() => {
    let cancelled = false;

    (async () => {
      if (typeof children !== 'string' || cancelled) {
        return;
      }

      try {
        mermaid.initialize({ startOnLoad: false, theme: theme === Theme.Dark ? 'dark' : 'default' });

        const { svg } = await mermaid.render(id, children);

        setDiagram(svg);
      } catch (error) {
        console.warn(error);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [children, theme, id]);

  return (
    <div className={classes.root}>
      <Code className="language-mermaid">{children}</Code>

      {diagram && <div dangerouslySetInnerHTML={{ __html: diagram }} className={classes.diagram} />}
    </div>
  );
}
