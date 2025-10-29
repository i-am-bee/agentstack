/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import Link, { type LinkProps } from 'next/link';
import type { PropsWithChildren } from 'react';

import { useRouteTransition } from '#contexts/TransitionContext/index.ts';

interface Props extends LinkProps {
  className?: string;
}

export function TransitionLink({ href, children, ...props }: PropsWithChildren<Props>) {
  const { transitionTo } = useRouteTransition();

  return (
    <Link
      href={href}
      prefetch={true}
      {...props}
      onClick={(e) => {
        e.preventDefault();
        transitionTo(String(href), { scroll: props.scroll });
      }}
    >
      {children}
    </Link>
  );
}
