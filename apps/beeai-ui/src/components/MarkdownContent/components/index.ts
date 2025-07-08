/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { JSX } from 'react';
import type { Components } from 'react-markdown';

import type { CitationLinkBaseProps } from './CitationLink/CitationLink';
import { Code } from './Code';
import { ExternalLink, type ExternalLinkProps } from './ExternalLink';
import { Img } from './Img';
import { Table } from './Table';

export interface ExtendedComponents extends Components {
  citationLink?: (props: CitationLinkBaseProps) => JSX.Element;
  externalLink?: (props: ExternalLinkProps) => JSX.Element;
}

export const components = {
  code: Code,
  table: Table,
  img: Img,
  externalLink: ExternalLink,
} satisfies ExtendedComponents;
