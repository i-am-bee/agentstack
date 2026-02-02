/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, ButtonSet } from '@carbon/react';

import { Layout } from '../components/Layout/Layout';
import { PageHeading } from '../components/PageHeading/PageHeading';
import Template from '../layout/Template';
import type { CustomPageProps } from '../types';
import classes from './Terms.module.scss';

export default function Terms(props: CustomPageProps<{ pageId: 'terms.ftl' }>) {
  const { kcContext, i18n } = props;

  const { msg, msgStr } = i18n;

  const { url } = kcContext;

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        displayMessage={false}
        headerNode={<PageHeading>Terms and Conditions</PageHeading>}
        centered
      >
        <div className={classes.content}>
          <div className={classes.termsText}>{msg('termsText')}</div>

          <form action={url.loginAction} method="POST">
            <ButtonSet>
              <Button name="accept" id="kc-accept" type="submit" kind="primary">
                {msgStr('doAccept')}
              </Button>
              <Button name="cancel" id="kc-decline" type="submit" kind="secondary">
                {msgStr('doDecline')}
              </Button>
            </ButtonSet>
          </form>
        </div>
      </Template>
    </Layout>
  );
}
