/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Send } from '@carbon/icons-react';
import { Button, IconButton, TextInput } from '@carbon/react';
import { FloatingFocusManager, FloatingPortal } from '@floating-ui/react';
import { AnimatePresence, motion } from 'framer-motion';
import { useId, useState } from 'react';

import { fadeProps } from '#utils/fadeProps.ts';

import type { MarkdownSelectionDialogReturn } from './hooks/useMarkdownSelectionDialog';
import classes from './Toolbar.module.scss';

interface Props {
  dialog: MarkdownSelectionDialogReturn;
  onAction: () => void;
}

export function Toolbar({ dialog, onAction }: Props) {
  const { isOpen, context } = dialog;

  return (
    <AnimatePresence>
      {isOpen && (
        <FloatingPortal>
          <FloatingFocusManager context={context} modal={false}>
            <ToolbarContent dialog={dialog} onAction={onAction} />
          </FloatingFocusManager>
        </FloatingPortal>
      )}
    </AnimatePresence>
  );
}

function ToolbarContent({ dialog, onAction }: Props) {
  const id = useId();

  const [view, setView] = useState<ToolbarView>(ToolbarView.Main);

  const { refs, floatingStyles, getFloatingProps } = dialog;

  return (
    <div ref={refs.setFloating} style={floatingStyles} {...getFloatingProps()}>
      <motion.div {...fadeProps()} className={classes.root}>
        {view === ToolbarView.Main ? (
          <Button size="sm" kind="primary" onClick={() => setView(ToolbarView.Ask)}>
            Ask agent
          </Button>
        ) : (
          <div className={classes.askForm}>
            <TextInput placeholder="How do you want to change it?" id={id} labelText="" autoFocus />
            <IconButton label="Ask agent" onClick={onAction} kind="ghost" size="sm">
              <Send />
            </IconButton>
          </div>
        )}
      </motion.div>
    </div>
  );
}

enum ToolbarView {
  Main = 'Main',
  Ask = 'Ask',
}
