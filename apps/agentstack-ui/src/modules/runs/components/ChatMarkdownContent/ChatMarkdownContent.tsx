/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { JSX } from 'react';
import { useMemo } from 'react';
import type { Components } from 'react-markdown';

import type { MarkdownContentProps } from '#components/MarkdownContent/MarkdownContent.tsx';
import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import { MessageCanvasCard, type MessageCanvasCardProps } from '#modules/canvas/components/MessageCanvasCard.tsx';
import type { UISourcePart } from '#modules/messages/types.ts';
import type { CitationLinkBaseProps } from '#modules/runs/components/ChatMarkdownContent/CitationLink/CitationLink.tsx';
import { CitationLink } from '#modules/runs/components/ChatMarkdownContent/CitationLink/CitationLink.tsx';

import { remarkCanvasLink } from './CanvasLink/remarkCanvasLink';
import { remarkCitationLink } from './CitationLink/remarkCitationLink';

interface ChatComponents extends Components {
  citationLink?: (props: CitationLinkBaseProps) => JSX.Element;
  canvasLink?: (props: MessageCanvasCardProps) => JSX.Element;
}

interface Props extends Omit<MarkdownContentProps, 'remarkPlugins' | 'components'> {
  sources?: UISourcePart[];
}

const remarkPlugins = [remarkCitationLink, remarkCanvasLink];

export function ChatMarkdownContent({ sources, ...props }: Props) {
  const components: ChatComponents = useMemo(
    () => ({
      citationLink: ({ ...props }) => <CitationLink {...props} sources={sources} />,
      canvasLink: ({ ...props }) => <MessageCanvasCard {...props} />,
    }),
    [sources],
  );

  return <MarkdownContent {...props} components={components} remarkPlugins={remarkPlugins} />;
}
