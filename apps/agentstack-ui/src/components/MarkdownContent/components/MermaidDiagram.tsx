/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { InlineLoading, InlineNotification } from '@carbon/react';
import { type HTMLAttributes, useEffect, useId } from 'react';
import type { ExtraProps } from 'react-markdown';

import { useTheme } from '#contexts/Theme/index.ts';
import { Theme } from '#contexts/Theme/types.ts';
import { usePrevious } from '#hooks/usePrevious.ts';

import { useMermaid } from '../contexts';
import { Code } from './Code';
import classes from './MermaidDiagram.module.scss';

export type MermaidDiagramProps = HTMLAttributes<HTMLElement> &
  ExtraProps & { mermaidIndex?: number; isStreaming?: boolean };

export function MermaidDiagram({ children, mermaidIndex, isStreaming }: MermaidDiagramProps) {
  const id = useId();
  const { theme } = useTheme();
  const { diagrams, setDiagram, mermaidApi, setMermaidApi } = useMermaid();

  if (mermaidIndex === undefined) {
    console.error('MermaidDiagram component requires a `mermaidIndex` prop.');
  }
  const index = mermaidIndex ?? 0;

  const diagram = diagrams.get(index);

  const themePrevious = usePrevious(theme);
  useEffect(() => {
    let isMounted = true;
    const hasThemeChanged = themePrevious && theme !== themePrevious;

    async function renderDiagram() {
      if (typeof children !== 'string') {
        return;
      }

      try {
        let api = mermaidApi;
        if (!api || hasThemeChanged) {
          api = (await import('mermaid')).default;
          api.initialize({
            startOnLoad: false,
            theme: theme === Theme.Dark ? 'dark' : 'default',
            suppressErrorRendering: true,
          });

          setMermaidApi(api);
        }

        const { svg } = await api.render(id, children);

        if (isMounted) {
          setDiagram(index, svg);
        }
      } catch (error) {
        if (isMounted && !isStreaming) {
          console.warn(error);
          setDiagram(index, error instanceof Error ? error : new Error('Unknown error rendering Mermaid diagram'));
        }
      }
    }

    renderDiagram();

    return () => {
      isMounted = false;
    };
  }, [children, theme, themePrevious, id, setDiagram, index, isStreaming, mermaidApi, setMermaidApi]);

  return (
    <div className={classes.root}>
      <Code className="language-mermaid">{children}</Code>

      {typeof diagram === 'string' ? (
        <div dangerouslySetInnerHTML={{ __html: diagram }} className={classes.diagram} />
      ) : diagram instanceof Error && !isStreaming ? (
        <InlineNotification
          kind="error"
          title={'Failed to render Mermaid diagram'}
          subtitle={diagram.message}
          lowContrast
          className={classes.error}
        />
      ) : (
        <div className={classes.loading}>
          <InlineLoading description="Rendering diagram..." />
        </div>
      )}
    </div>
  );
}
