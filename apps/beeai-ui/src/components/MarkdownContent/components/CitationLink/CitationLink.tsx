/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import type { UISourcePart } from '#modules/messages/types.ts';

import { InlineCitations } from './InlineCitations';

export interface CitationLinkBaseProps extends PropsWithChildren {
  items: string[];
}

interface CitationLinkProps extends CitationLinkBaseProps {
  sources: UISourcePart[] | undefined;
}

export function CitationLink({ sources, items, children }: CitationLinkProps) {
  const filteredSources = sources?.filter(({ id }) => items.includes(id));

  return <InlineCitations sources={filteredSources}>{children}</InlineCitations>;
}
