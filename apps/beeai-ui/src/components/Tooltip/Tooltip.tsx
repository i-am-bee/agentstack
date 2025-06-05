/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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
