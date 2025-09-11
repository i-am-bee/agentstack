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

import { useAgentRun } from '../contexts/agent-run';
import classes from './RunSettings.module.scss';
import { RunSettingsForm } from './RunSettingsForm';
import { useRunSettingsDialog } from './useRunSettingsDialog';

interface Props {
  containerRef: RefObject<HTMLElement | null>;
}

export function RunSettings({ containerRef }: Props) {
  const { settingsRender, hasMessages } = useAgentRun();

  const { isOpen, refs, floatingStyles, context, getReferenceProps, getFloatingProps } = useRunSettingsDialog({
    containerRef,
  });

  if (!settingsRender?.fields.length) {
    return null;
  }

  return (
    <div className={classes.root}>
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
                      transform: `translateY(${hasMessages ? '1' : '-1'}rem)`,
                    },
                    visible: {
                      transform: 'translateY(0)',
                    },
                  })}
                  className={classes.content}
                >
                  <RunSettingsForm settingsRender={settingsRender} />
                </motion.div>
              </div>
            </FloatingFocusManager>
          </FloatingPortal>
        )}
      </AnimatePresence>
    </div>
  );
}
