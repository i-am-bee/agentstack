/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { JSX } from 'react';
import type { Components } from 'react-markdown';

import type { CitationLinkProperties } from '#modules/runs/sources/types.ts';

import { Code } from './Code';
import { Img } from './Img';
import { Table } from './Table';

export interface ExtendedComponents extends Components {
  citationLink?: (props: CitationLinkProperties) => JSX.Element;
}

export const components = {
  code: Code,
  table: Table,
  img: Img,
};
