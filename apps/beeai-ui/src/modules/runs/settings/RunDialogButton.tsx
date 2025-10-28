/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ChevronDown } from '@carbon/icons-react';
import { Button, IconButton } from '@carbon/react';
import { FloatingFocusManager, FloatingPortal } from '@floating-ui/react';
import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import type { ComponentType, PropsWithChildren } from 'react';

import { fadeProps } from '#utils/fadeProps.ts';

import { useAgentRun } from '../contexts/agent-run';
import classes from './RunDialogButton.module.scss';
import type { RunSettingsDialogReturn } from './useRunSettingsDialog';

interface Props {
  dialog: RunSettingsDialogReturn;
  useButtonReference?: boolean;
  label: string;
  icon: ComponentType;
  iconOnly?: boolean;
}

export function RunDialogButton({
  dialog,
  useButtonReference,
  children,
  label,
  icon: Icon,
  iconOnly,
}: PropsWithChildren<Props>) {
  const { hasMessages } = useAgentRun();

  const { isOpen, refs, floatingStyles, context, getReferenceProps, getFloatingProps } = dialog;

  return (
    <div className={classes.root}>
      {iconOnly ? (
        <IconButton
          kind="ghost"
          size="sm"
          label={label}
          autoAlign
          align="top"
          ref={useButtonReference ? refs.setPositionReference : null}
          {...getReferenceProps()}
        >
          <Icon />
        </IconButton>
      ) : (
        <Button
          kind="ghost"
          size="xs"
          className={clsx(classes.button, { [classes.isOpen]: isOpen })}
          {...getReferenceProps()}
          ref={useButtonReference ? refs.setPositionReference : null}
        >
          <Icon />
          {label}
          <ChevronDown className={classes.statusIcon} />
        </Button>
      )}

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
                  {children}
                </motion.div>
              </div>
            </FloatingFocusManager>
          </FloatingPortal>
        )}
      </AnimatePresence>
    </div>
  );
}
