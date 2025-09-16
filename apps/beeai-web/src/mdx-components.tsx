/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Code } from '@i-am-bee/beeai-ui';
import type { MDXComponents } from 'mdx/types';

const components: MDXComponents = {
  pre: ({ children }) => children,
  code: ({ ...props }) => <Code {...props} variant="blog" />,
};

export function useMDXComponents(defaultComponents: MDXComponents): MDXComponents {
  return {
    ...defaultComponents,
    ...components,
  };
}
