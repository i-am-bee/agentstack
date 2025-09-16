/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ChevronDown } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import { type PropsWithChildren, useState } from 'react';

import { useScrollbarWidth } from '#hooks/useScrollbarWidth.ts';
import { createScrollbarStyles } from '#utils/createScrollbarStyles.ts';
import { fadeProps } from '#utils/fadeProps.ts';

import classes from './NavGroup.module.scss';

interface Props extends PropsWithChildren {
  heading?: string;
  toggleable?: boolean;
  className?: string;
  bodyClassName?: string;
}

export function NavGroup({ heading, toggleable, className, bodyClassName, children }: Props) {
  const [isOpen, setIsOpen] = useState(true);
  const { ref, scrollbarWidth } = useScrollbarWidth();

  return (
    <nav className={clsx(classes.root, className, { [classes.toggleable]: toggleable })}>
      {(heading || toggleable) && (
        <div className={classes.header}>
          {heading && <h2 className={classes.heading}>{heading}</h2>}

          {toggleable && (
            <IconButton
              label="Toggle"
              size="sm"
              kind="ghost"
              wrapperClasses={clsx(classes.toggle, { [classes.isOpen]: isOpen })}
              onClick={() => setIsOpen((state) => !state)}
            >
              <ChevronDown />
            </IconButton>
          )}
        </div>
      )}

      <AnimatePresence>
        {isOpen && (
          <motion.div
            {...fadeProps()}
            {...createScrollbarStyles({ width: scrollbarWidth })}
            ref={ref}
            className={clsx(classes.body, bodyClassName)}
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
