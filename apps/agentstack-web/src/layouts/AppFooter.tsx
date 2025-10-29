/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { LF_PROJECTS_LINK } from '@i-am-bee/agentstack-ui';

import { APP_NAME } from '@/constants';

import { FooterNav } from '../components/FooterNav/FooterNav';
import classes from './AppFooter.module.scss';
import { LayoutContainer } from './LayoutContainer';

export function AppFooter() {
  return (
    <footer>
      <LayoutContainer asGrid>
        <div className={classes.root}>
          <p className={classes.copyright}>
            Copyright © {APP_NAME} a Series of LF Projects, LLC
            <br />
            For web site terms of use, trademark policy and other project policies please see{' '}
            <a href={LF_PROJECTS_LINK} target="_blank" rel="noreferrer">
              {LF_PROJECTS_LINK}
            </a>
            .
          </p>

          <FooterNav className={classes.communityNav} />
        </div>
      </LayoutContainer>
    </footer>
  );
}
