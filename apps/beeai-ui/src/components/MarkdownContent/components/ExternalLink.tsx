/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AnchorHTMLAttributes } from 'react';
import type { ExtraProps } from 'react-markdown';

export type ExternalLinkProps = AnchorHTMLAttributes<HTMLAnchorElement> & ExtraProps;

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function ExternalLink({ node, ...props }: ExternalLinkProps) {
  return <a {...props} target="_blank" rel="noreferrer" />;
}
