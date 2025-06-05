/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import Link, { LinkProps } from 'next/link';
import { PropsWithChildren } from 'react';

import { useRouteTransition } from '../../../../beeai-ui/src/contexts/TransitionContext';

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
