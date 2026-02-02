/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, Checkbox } from '@carbon/react';
import { useState } from 'react';

import { Layout } from '../components/Layout/Layout';
import { PageHeading } from '../components/PageHeading/PageHeading';
import Template from '../layout/Template';
import type { CustomPageProps, UserProfileFormPageProps } from '../types';
import UserProfileFormFields from '../UserProfileFormFields';
import classes from './UpdateEmail.module.scss';

export default function UpdateEmail(props: CustomPageProps<{ pageId: 'update-email.ftl' }> & UserProfileFormPageProps) {
  const { kcContext, i18n, doMakeUserConfirmPassword } = props;
  const { url, messagesPerField, isAppInitiatedAction } = kcContext;
  const { msg } = i18n;

  const [isFormSubmittable, setIsFormSubmittable] = useState(false);

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        displayMessage={messagesPerField.exists('global')}
        headerNode={<PageHeading>{msg('updateEmailTitle')}</PageHeading>}
      >
        <div className={classes.content}>
          <form className={classes.form} action={url.loginAction} method="post">
            <UserProfileFormFields
              kcContext={kcContext}
              i18n={i18n}
              onIsFormSubmittableValueChange={setIsFormSubmittable}
              doMakeUserConfirmPassword={doMakeUserConfirmPassword}
              kcClsx={() => ''}
            />

            <Checkbox
              id="logout-sessions"
              name="logout-sessions"
              labelText={msg('logoutOtherSessions')}
              defaultChecked
            />

            <div className={classes.actions}>
              <Button type="submit" disabled={!isFormSubmittable}>
                {msg('doSubmit')}
              </Button>
              {isAppInitiatedAction && (
                <Button kind="secondary" type="submit" name="cancel-aia" value="true">
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
