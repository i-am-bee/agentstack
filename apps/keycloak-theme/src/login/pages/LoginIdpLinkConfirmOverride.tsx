/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, Link } from '@carbon/react';

import { Layout } from '../components/Layout/Layout';
import { PageHeading } from '../components/PageHeading/PageHeading';
import Template from '../layout/Template';
import type { CustomPageProps } from '../types';
import classes from './LoginIdpLinkConfirmOverride.module.scss';

export default function LoginIdpLinkConfirmOverride(
  props: CustomPageProps<{ pageId: 'login-idp-link-confirm-override.ftl' }>,
) {
  const { kcContext, i18n } = props;

  const { url, idpDisplayName } = kcContext;

  const { msg } = i18n;

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        headerNode={<PageHeading>{msg('confirmOverrideIdpTitle')}</PageHeading>}
        centered
        size="sm"
      >
        <div className={classes.root}>
          <p>
            {msg('pageExpiredMsg1')}{' '}
            <Link id="loginRestartLink" href={url.loginRestartFlowUrl}>
              {msg('doClickHere')}
            </Link>
          </p>
          <form action={url.loginAction} method="post">
            <Button type="submit" kind="primary" name="submitAction" id="confirmOverride" value="confirmOverride">
              {msg('confirmOverrideIdpContinue', idpDisplayName)}
            </Button>
          </form>
        </div>
      </Template>
    </Layout>
  );
}
