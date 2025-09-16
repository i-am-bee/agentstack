/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ChevronDown } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import clsx from 'clsx';
import truncate from 'lodash/truncate';
import type { TransitionEventHandler } from 'react';
import { useCallback, useState } from 'react';

import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { isNotNull } from '#utils/helpers.ts';

import classes from './TrajectoryItem.module.scss';
import { TrajectoryItemContent } from './TrajectoryItemContent';

interface Props {
  trajectory: UITrajectoryPart;
}

export function TrajectoryItem({ trajectory }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  const { title, content } = trajectory;

  const isToggleable = isNotNull(content);

  const handleToggle = useCallback(() => {
    setIsAnimating(true);
    setIsOpen((state) => !state);
  }, []);

  const handleTransitionEnd: TransitionEventHandler = useCallback((event) => {
    const { target, currentTarget, propertyName } = event;

    if (target === currentTarget && propertyName === 'grid-template-rows') {
      setIsAnimating(false);
    }
  }, []);

  return (
    <div
      className={clsx(classes.root, {
        [classes.isOpen]: isOpen,
        [classes.isAnimating]: isAnimating,
      })}
    >
      <header className={classes.header}>
        {isToggleable && (
          <IconButton
            kind="ghost"
            size="sm"
            label={isOpen ? 'Collapse' : 'Expand'}
            wrapperClasses={classes.button}
            onClick={handleToggle}
          >
            <ChevronDown />
          </IconButton>
        )}

        {title && (
          <h3 className={classes.name}>
            {/* <span className={classes.icon}>
            <Icon />
          </span> */}

            <span>{title}</span>
          </h3>
        )}

        {content && <div className={classes.message}>{truncate(content, { length: MAX_CONTENT_PREVIEW_LENGTH })}</div>}
      </header>

      {isToggleable && (
        <div className={classes.body} onTransitionEnd={handleTransitionEnd}>
          <div className={classes.panel}>
            <TrajectoryItemContent trajectory={trajectory} />
          </div>
        </div>
      )}
    </div>
  );
}

const MAX_CONTENT_PREVIEW_LENGTH = 120;
