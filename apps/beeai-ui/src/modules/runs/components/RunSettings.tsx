/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Settings } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import { FloatingFocusManager, FloatingPortal } from '@floating-ui/react';
import { AnimatePresence, motion } from 'framer-motion';
import type { RefObject } from 'react';

import { fadeProps } from '#utils/fadeProps.ts';

import { ChatTools } from '../chat/ChatTools';
import { useRunSettingsDialog } from '../hooks/useRunSettingsDialog';
import classes from './RunSettings.module.scss';

interface Props {
  containerRef: RefObject<HTMLElement | null>;
}

export function RunSettings({ containerRef }: Props) {
  const { isOpen, refs, floatingStyles, context, getReferenceProps, getFloatingProps } = useRunSettingsDialog({
    containerRef,
  });

  return (
    <div className={classes.root}>
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
                <div ref={refs.setFloating} style={floatingStyles} className={classes.modal} {...getFloatingProps()}>
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
    </div>
  );
}
