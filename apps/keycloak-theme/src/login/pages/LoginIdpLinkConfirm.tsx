/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, ButtonSet } from '@carbon/react';

import { Layout } from '../components/Layout/Layout';
import { PageHeading } from '../components/PageHeading/PageHeading';
import Template from '../layout/Template';
import type { CustomPageProps } from '../types';

export default function LoginIdpLinkConfirm(props: CustomPageProps<{ pageId: 'login-idp-link-confirm.ftl' }>) {
  const { kcContext, i18n } = props;

  const { url, idpAlias } = kcContext;

  const { msg } = i18n;

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        headerNode={<PageHeading>{msg('confirmLinkIdpTitle')}</PageHeading>}
        centered
        size="sm"
      >
        <div>
          <form action={url.loginAction} method="post">
            <ButtonSet>
              <Button type="submit" kind="secondary" name="submitAction" id="updateProfile" value="updateProfile">
                {msg('confirmLinkIdpReviewProfile')}
              </Button>
              <Button type="submit" kind="primary" name="submitAction" id="linkAccount" value="linkAccount">
                {msg('confirmLinkIdpContinue', idpAlias)}
              </Button>
            </ButtonSet>
          </form>
        </div>
      </Template>
    </Layout>
  );
}
