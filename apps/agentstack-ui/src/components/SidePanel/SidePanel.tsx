/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Close } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import clsx from 'clsx';
import type { PropsWithChildren } from 'react';

import { useApp } from '#contexts/App/index.ts';
import { useScrollbar } from '#hooks/useScrollbar.ts';

import classes from './SidePanel.module.scss';

interface Props extends PropsWithChildren {
  isOpen?: boolean;
  showCloseButton?: boolean;
  className?: string;
}

export function SidePanel({ isOpen, showCloseButton, className, children }: Props) {
  const { closeSidePanel } = useApp();
  const scrollbarProps = useScrollbar();

  return (
    <aside className={clsx(classes.root, { [classes.isOpen]: isOpen }, className)}>
      <div className={classes.content} {...scrollbarProps}>
        {showCloseButton && (
          <IconButton
            kind="ghost"
            size="sm"
            label="Close"
            align="left"
            wrapperClasses={classes.closeButton}
            onClick={closeSidePanel}
          >
            <Close />
          </IconButton>
        )}

        {children}
      </div>
    </aside>
  );
}
