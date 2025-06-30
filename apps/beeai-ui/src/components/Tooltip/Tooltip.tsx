/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Placement } from '@floating-ui/react';
import {
  arrow,
  autoUpdate,
  flip,
  FloatingArrow,
  FloatingPortal,
  offset,
  safePolygon,
  shift,
  useDismiss,
  useFloating,
  useFocus,
  useHover,
  useInteractions,
  useRole,
} from '@floating-ui/react';
import { Slot } from '@radix-ui/react-slot';
import clsx from 'clsx';
import type { PropsWithChildren, ReactNode } from 'react';
import { useRef, useState } from 'react';

import classes from './Tooltip.module.scss';

interface Props {
  content: ReactNode;
  placement?: Placement;
  size?: 'sm' | 'md' | 'lg';
  asChild?: boolean;
}

export function Tooltip({ content, placement = 'bottom', size = 'md', asChild, children }: PropsWithChildren<Props>) {
  const arrowRef = useRef(null);

  const SIZE = {
    sm: {
      ArrowWidth: 8,
      ArrowHeight: 4,
      Offset: 3,
    },
    md: {
      ArrowWidth: 12,
      ArrowHeight: 6,
      Offset: 8,
    },
    lg: {
      ArrowWidth: 12,
      ArrowHeight: 6,
      Offset: 8,
    },
  }[size];

  const [isOpen, setIsOpen] = useState(false);

  const { refs, floatingStyles, context } = useFloating({
    placement,
    open: isOpen,
    onOpenChange: setIsOpen,
    whileElementsMounted: autoUpdate,
    middleware: [
      offset(SIZE.ArrowHeight + SIZE.Offset),
      flip({
        fallbackAxisSideDirection: 'start',
      }),
      shift(),
      arrow({
        element: arrowRef,
      }),
    ],
  });

  const hover = useHover(context, { move: false, handleClose: safePolygon() });
  const focus = useFocus(context);
  const dismiss = useDismiss(context);
  const role = useRole(context, { role: 'tooltip' });

  const { getReferenceProps, getFloatingProps } = useInteractions([hover, focus, dismiss, role]);

  const Comp = asChild ? Slot : 'button';

  return (
    <>
      <Comp ref={refs.setReference} {...getReferenceProps()}>
        {children}
      </Comp>

      {isOpen && (
        <FloatingPortal>
          <div
            ref={refs.setFloating}
            style={floatingStyles}
            className={clsx(classes.root, { [classes[size]]: size })}
            {...getFloatingProps()}
          >
            <div className={classes.content}>{content}</div>

            <FloatingArrow
              ref={arrowRef}
              context={context}
              width={SIZE.ArrowWidth}
              height={SIZE.ArrowHeight}
              className={classes.arrow}
            />
          </div>
        </FloatingPortal>
      )}
    </>
  );
}
