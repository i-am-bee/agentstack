/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Add } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import clsx from 'clsx';
import type { PropsWithChildren } from 'react';

import { useScrollbar } from '#hooks/useScrollbar.ts';

import classes from './NavGroup.module.scss';

interface Props extends PropsWithChildren {
  heading?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function NavGroup({ heading, action, className, children }: Props) {
  const scrollbarProps = useScrollbar();

  return (
    <nav className={clsx(classes.root, className)}>
      {(heading || action) && (
        <div className={classes.header}>
          {heading && <h2 className={classes.heading}>{heading}</h2>}

          {action && (
            <IconButton
              kind="ghost"
              size="xs"
              label={action.label}
              wrapperClasses={classes.action}
              onClick={action.onClick}
            >
              <Add />
            </IconButton>
          )}
        </div>
      )}

      <div className={classes.body} {...scrollbarProps}>
        {children}
      </div>
    </nav>
  );
}
