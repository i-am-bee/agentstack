/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import clsx from 'clsx';
import { useRouter } from 'next/navigation';
import type { TransitionEvent, TransitionEventHandler } from 'react';
import { useRef, useState } from 'react';

import { useApp } from '#contexts/App/index.ts';
import { useParamsFromUrl } from '#hooks/useParamsFromUrl.ts';
import { routes } from '#utils/router.ts';

import { FooterNav } from './FooterNav';
import classes from './Navbar.module.scss';
import { NavbarButton } from './NavbarButton';
import { NavbarMainContent } from './NavbarMainContent';
import NewSession from './NewSession.svg';
import { SessionsButton } from './SessionsButton';
import { ToggleNavbarButton } from './ToggleNavbarButton';

interface Props {
  className?: string;
}

export function Navbar({ className }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [isAnimating, setIsAnimating] = useState(false);

  const router = useRouter();
  const { providerId } = useParamsFromUrl();

  const { navbarOpen } = useApp();

  const checkTransition = (event: TransitionEvent) => {
    const {
      target,
      currentTarget,
      nativeEvent: { propertyName },
    } = event;

    return target === currentTarget && propertyName === 'width';
  };

  const handleTransitionStart: TransitionEventHandler = (event) => {
    if (checkTransition(event)) {
      setIsAnimating(true);
    }
  };

  const handleTransitionEnd: TransitionEventHandler = (event) => {
    if (checkTransition(event)) {
      setIsAnimating(false);
    }
  };

  if (!providerId) {
    return null;
  }

  return (
    <div
      ref={ref}
      className={clsx(classes.root, className, {
        [classes.isOpen]: navbarOpen,
        [classes.isAnimating]: isAnimating,
      })}
      onTransitionStart={handleTransitionStart}
      onTransitionEnd={handleTransitionEnd}
    >
      <div className={classes.content}>
        <header className={classes.stack}>
          <ToggleNavbarButton />

          <NavbarButton
            icon={NewSession}
            label="New Session"
            onClick={() => {
              router.push(routes.agentRun({ providerId }));
            }}
          />
        </header>

        <div className={classes.body}>
          <NavbarMainContent className={classes.mainContent} />
          <SessionsButton className={classes.sessionsButton} />
        </div>

        <footer className={classes.stack}>
          <FooterNav />
        </footer>
      </div>
    </div>
  );
}
