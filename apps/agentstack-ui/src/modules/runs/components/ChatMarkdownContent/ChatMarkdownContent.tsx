/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { JSX } from 'react';
import { useMemo } from 'react';
import type { Components } from 'react-markdown';

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import type { UISourcePart } from '#modules/messages/types.ts';
import type { CitationLinkBaseProps } from '#modules/runs/components/ChatMarkdownContent/CitationLink/CitationLink.tsx';
import { CitationLink } from '#modules/runs/components/ChatMarkdownContent/CitationLink/CitationLink.tsx';

import { remarkCitationLink } from './CitationLink/remarkCitationLink';

interface Props {
  codeBlocksExpanded?: boolean;
  sources?: UISourcePart[];
  children?: string;
  className?: string;
}

export function ChatMarkdownContent({ sources, ...props }: Props) {
  const components: ChatComponents = useMemo(
    () => ({
      citationLink: ({ ...props }) => <CitationLink {...props} sources={sources} />,
    }),
    [sources],
  );

  return <MarkdownContent {...props} components={components} remarkPlugins={remarkPlugins} />;
}

const remarkPlugins = [remarkCitationLink];

export interface ChatComponents extends Components {
  citationLink?: (props: CitationLinkBaseProps) => JSX.Element;
}
