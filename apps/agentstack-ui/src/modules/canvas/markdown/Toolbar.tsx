/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from '@carbon/react';
import { FloatingPortal } from '@floating-ui/react';
import { AnimatePresence, motion } from 'framer-motion';
import { useState } from 'react';

import { fadeProps } from '#utils/fadeProps.ts';

import { CanvasEditForm } from './CanvasEditForm';
import type { MarkdownSelectionDialogReturn } from './hooks/useMarkdownSelectionDialog';
import classes from './Toolbar.module.scss';

interface Props {
  dialog: MarkdownSelectionDialogReturn;
  onEditRequest: (description: string) => void;
}

export function Toolbar({ dialog, onEditRequest }: Props) {
  const { isOpen } = dialog;

  return (
    <AnimatePresence>
      {isOpen && (
        <FloatingPortal>
          <ToolbarContent dialog={dialog} onEditRequest={onEditRequest} />
        </FloatingPortal>
      )}
    </AnimatePresence>
  );
}

function ToolbarContent({ dialog, onEditRequest }: Props) {
  const [view, setView] = useState<ToolbarView>(ToolbarView.Main);

  const { refs, floatingStyles, getFloatingProps, close } = dialog;

  return (
    <div ref={refs.setFloating} style={floatingStyles} {...getFloatingProps()}>
      <motion.div {...fadeProps()} className={classes.root}>
        {view === ToolbarView.Main ? (
          <Button size="sm" kind="primary" onClick={() => setView(ToolbarView.Ask)}>
            Ask agent
          </Button>
        ) : (
          <CanvasEditForm
            onSubmit={(description) => {
              onEditRequest(description);
              close();
            }}
          />
        )}
      </motion.div>
    </div>
  );
}

enum ToolbarView {
  Main = 'Main',
  Ask = 'Ask',
}
