/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Slot } from '@radix-ui/react-slot';
import type { HTMLProps } from 'react';

import { useViewTransition } from '#hooks/useViewTransition.ts';

interface Props extends Omit<HTMLProps<HTMLAnchorElement>, 'href'> {
  href?: string;
  asChild?: boolean;
}

export function TransitionLink({ href, onClick, asChild, children, ...props }: Props) {
  const { transitionTo } = useViewTransition();

  const Element = asChild ? Slot : 'a';

  return (
    <Element
      {...props}
      href={href}
      onClick={(e) => {
        if (href) {
          transitionTo(href);
        }
        onClick?.(e);
        e.preventDefault();
      }}
    >
      {children}
    </Element>
  );
}
