/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { InlineLoading } from '@carbon/react';
import mermaid from 'mermaid';
import { type HTMLAttributes, useEffect, useId } from 'react';
import type { ExtraProps } from 'react-markdown';

import { useTheme } from '#contexts/Theme/index.ts';
import { Theme } from '#contexts/Theme/types.ts';

import { useMermaid } from '../contexts';
import { Code } from './Code';
import classes from './MermaidDiagram.module.scss';

export type MermaidDiagramProps = HTMLAttributes<HTMLElement> & ExtraProps & { mermaidIndex?: number };

export function MermaidDiagram({ children, ...props }: MermaidDiagramProps) {
  const id = useId();
  const { theme } = useTheme();
  const { diagrams, setDiagram } = useMermaid();

  const index = props.mermaidIndex ?? 0;
  const diagram = diagrams.get(index);

  useEffect(() => {
    mermaid.initialize({ startOnLoad: false, theme: theme === Theme.Dark ? 'dark' : 'default' });
  }, [theme]);

  useEffect(() => {
    let isMounted = true;

    async function renderDiagram() {
      if (typeof children !== 'string') {
        return;
      }

      try {
        const { svg } = await mermaid.render(id, children);

        if (isMounted) {
          setDiagram(index, svg);
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
  }, [children, theme, id, setDiagram, index]);

  return (
    <div className={classes.root}>
      <Code className="language-mermaid">{children}</Code>

      {diagram ? (
        <div dangerouslySetInnerHTML={{ __html: diagram }} className={classes.diagram} />
      ) : (
        <div className={classes.loading}>
          <InlineLoading description="Rendering diagram..." />
        </div>
      )}
    </div>
  );
}
