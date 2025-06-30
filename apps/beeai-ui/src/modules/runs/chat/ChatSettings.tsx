/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Settings } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import {
  autoUpdate,
  FloatingFocusManager,
  FloatingPortal,
  offset,
  size,
  useClick,
  useDismiss,
  useFloating,
  useInteractions,
  useRole,
} from '@floating-ui/react';
import { AnimatePresence, motion } from 'framer-motion';
import type { RefObject } from 'react';
import { useState } from 'react';

import { fadeProps } from '#utils/fadeProps.ts';

import classes from './ChatSettings.module.scss';
import { ChatTools } from './ChatTools';

interface Props {
  containerRef: RefObject<HTMLElement | null>;
}

export function ChatSettings({ containerRef }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  const { refs, floatingStyles, context } = useFloating({
    placement: 'top-start',
    open: isOpen,
    onOpenChange: setIsOpen,
    whileElementsMounted: autoUpdate,
    middleware: [
      offset(OFFSET),
      size({
        apply({ elements }) {
          const container = containerRef.current;

          if (container) {
            Object.assign(elements.floating.style, {
              maxWidth: `${container.offsetWidth}px`,
            });
          }
        },
      }),
    ],
  });

  const click = useClick(context);
  const dismiss = useDismiss(context);
  const role = useRole(context, { role: 'dialog' });

  const { getReferenceProps, getFloatingProps } = useInteractions([click, dismiss, role]);

  return (
    <>
      <IconButton
        kind="ghost"
        size="sm"
        label="Customize Tools"
        autoAlign
        ref={refs.setReference}
        {...getReferenceProps()}
      >
        <Settings />
      </IconButton>

      <AnimatePresence>
        {isOpen && (
          <FloatingPortal>
            <FloatingFocusManager context={context}>
              <div ref={refs.setFloating} style={floatingStyles} className={classes.root} {...getFloatingProps()}>
                <motion.div
                  {...fadeProps({
                    hidden: {
                      transform: 'translateY(1rem)',
                    },
                    visible: {
                      transform: 'translateY(0)',
                    },
                  })}
                >
                  <div className={classes.content}>
                    <ChatTools />
                  </div>
                </motion.div>
              </div>
            </FloatingFocusManager>
          </FloatingPortal>
        )}
      </AnimatePresence>
    </>
  );
}

const OFFSET = {
  mainAxis: 56,
  crossAxis: -12,
};
