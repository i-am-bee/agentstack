/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowUpRight } from '@carbon/icons-react';
import type { ButtonBaseProps } from '@carbon/react';
import { Button, ButtonSkeleton } from '@carbon/react';
import clsx from 'clsx';

import { TransitionLink } from '#components/TransitionLink/TransitionLink.tsx';

import classes from './NavItem.module.scss';

export interface NavItem {
  key: string;
  href: string;
  label: string;
  isActive?: boolean;
  isExternal?: boolean;
  target?: '_blank' | '_self';
}

type Props = Omit<NavItem, 'key'>;

export function NavItem({ href, label, isActive, isExternal, target = '_blank' }: Props) {
  const linkProps: ButtonBaseProps = {
    href,
    className: clsx(classes.button, { [classes.isActive]: isActive }),
    kind: 'ghost',
    size: 'sm',
  };

  return (
    <li>
      {isExternal ? (
        <Button {...linkProps} target={target} rel="noreferrer">
          {label}

          <ArrowUpRight />
        </Button>
      ) : (
        <Button {...linkProps} as={TransitionLink}>
          {label}
        </Button>
      )}
    </li>
  );
}

NavItem.Skeleton = function NavItemSkeleton() {
  return (
    <li>
      <ButtonSkeleton size="sm" className={classes.button} />
    </li>
  );
};
