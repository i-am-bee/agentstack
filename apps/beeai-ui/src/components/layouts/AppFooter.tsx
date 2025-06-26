/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { LF_PROJECTS_LINK } from '#utils/constants.ts';

import { FooterNav } from '../FooterNav/FooterNav';
import classes from './AppFooter.module.scss';
import { Container } from './Container';

interface Props {
  className?: string;
}

export function AppFooter({ className }: Props) {
  return (
    <footer className={className}>
      <Container size="max">
        <div className={classes.holder}>
          <p className={classes.copyright}>
            Copyright © BeeAI a Series of LF Projects, LLC
            <br />
            For web site terms of use, trademark policy and other project policies please see{' '}
            <a href={LF_PROJECTS_LINK} target="_blank" rel="noreferrer">
              {LF_PROJECTS_LINK}
            </a>
            .
          </p>

          <FooterNav className={classes.communityNav} />
        </div>
      </Container>
    </footer>
  );
}
