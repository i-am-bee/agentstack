/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, Checkbox, PasswordInput } from '@carbon/react';
import { kcSanitize } from 'keycloakify/lib/kcSanitize';

import { Layout } from '../components/Layout/Layout';
import { PageHeading } from '../components/PageHeading/PageHeading';
import Template from '../layout/Template';
import type { CustomPageProps } from '../types';
import classes from './LoginUpdatePassword.module.scss';

export default function LoginUpdatePassword(props: CustomPageProps<{ pageId: 'login-update-password.ftl' }>) {
  const { kcContext, i18n } = props;

  const { msg, msgStr } = i18n;

  const { url, messagesPerField, isAppInitiatedAction } = kcContext;

  const hasPasswordError = messagesPerField.existsError('password');
  const hasConfirmError = messagesPerField.existsError('password-confirm');

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        displayMessage={!hasPasswordError && !hasConfirmError}
        headerNode={<PageHeading>{msg('updatePasswordTitle')}</PageHeading>}
      >
        <div className={classes.content}>
          <form id="kc-passwd-update-form" className={classes.form} action={url.loginAction} method="post">
            <PasswordInput
              id="password-new"
              name="password-new"
              labelText={msgStr('passwordNew')}
              autoFocus
              autoComplete="new-password"
              invalid={hasPasswordError}
              invalidText={
                hasPasswordError ? (
                  <span
                    dangerouslySetInnerHTML={{
                      __html: kcSanitize(messagesPerField.get('password')),
                    }}
                  />
                ) : undefined
              }
            />

            <PasswordInput
              id="password-confirm"
              name="password-confirm"
              labelText={msgStr('passwordConfirm')}
              autoComplete="new-password"
              invalid={hasConfirmError}
              invalidText={
                hasConfirmError ? (
                  <span
                    dangerouslySetInnerHTML={{
                      __html: kcSanitize(messagesPerField.get('password-confirm')),
                    }}
                  />
                ) : undefined
              }
            />

            <Checkbox
              id="logout-sessions"
              name="logout-sessions"
              labelText={msgStr('logoutOtherSessions')}
              value="on"
              defaultChecked={true}
            />

            <div className={classes.actions}>
              <Button type="submit" kind="primary">
                {msgStr('doSubmit')}
              </Button>
              {isAppInitiatedAction && (
                <Button type="submit" kind="secondary" name="cancel-aia" value="true">
                  {msg('doCancel')}
                </Button>
              )}
            </div>
          </form>
        </div>
      </Template>
    </Layout>
  );
}
