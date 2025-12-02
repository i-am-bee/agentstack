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

export type MermaidDiagramProps = HTMLAttributes<HTMLElement> &
  ExtraProps & {
    showDiagram?: boolean;
  };

export function MermaidDiagram({ showDiagram = true, children }: MermaidDiagramProps) {
  const id = useId();
  const [diagram, setDiagram] = useState<string | null>(null);

  const { theme } = useTheme();

  useEffect(() => {
    mermaid.initialize({ startOnLoad: false, theme: theme === Theme.Dark ? 'dark' : 'default' });
  }, [theme]);

  useEffect(() => {
    let isMounted = true;

    async function renderDiagram() {
      if (!showDiagram || typeof children !== 'string') {
        return;
      }

      try {
        const { svg } = await mermaid.render(id, children);

        if (isMounted) {
          setDiagram(svg);
        }
      } catch (error) {
        if (isMounted) {
          console.warn(error);
        }
      }
    }

    renderDiagram();

    return () => {
      isMounted = false;
    };
  }, [showDiagram, children, theme, id]);

  return (
    <div className={classes.root}>
      <Code className="language-mermaid">{children}</Code>

      {showDiagram && diagram && <div dangerouslySetInnerHTML={{ __html: diagram }} className={classes.diagram} />}
    </div>
  );
}
