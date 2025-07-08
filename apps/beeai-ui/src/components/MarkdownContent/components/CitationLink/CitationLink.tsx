/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import type { SourceReference } from '#modules/runs/sources/api/types.ts';

import { InlineCitations } from './InlineCitations';

export interface CitationLinkBaseProps extends PropsWithChildren {
  keys: string[];
}

interface CitationLinkProps extends CitationLinkBaseProps {
  sources: SourceReference[] | undefined;
}

export function CitationLink({ sources, keys, children }: CitationLinkProps) {
  const filteredSources = sources?.filter(({ key }) => keys.includes(key));

  return <InlineCitations sources={filteredSources}>{children}</InlineCitations>;
}
