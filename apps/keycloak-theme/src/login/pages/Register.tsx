/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, Checkbox, Link } from '@carbon/react';
import { useLayoutEffect, useRef, useState } from 'react';

import { Layout } from '../components/Layout/Layout';
import { PageHeading } from '../components/PageHeading/PageHeading';
import type { I18n } from '../i18n';
import type { KcContext } from '../KcContext';
import Template from '../layout/Template';
import type { CustomPageProps, UserProfileFormPageProps } from '../types';
import UserProfileFormFields from '../UserProfileFormFields';
import { getAppName } from '../utils';
import classes from './Register.module.scss';

declare global {
  interface Window {
    onSubmitRecaptcha?: () => void;
  }
}

type RegisterProps = CustomPageProps<{ pageId: 'register.ftl' }> & UserProfileFormPageProps;

export default function Register(props: RegisterProps) {
  const { kcContext, i18n, doMakeUserConfirmPassword } = props;

  const {
    messageHeader,
    url,
    messagesPerField,
    recaptchaRequired,
    recaptchaVisible,
    recaptchaSiteKey,
    recaptchaAction,
    termsAcceptanceRequired,
    realm,
  } = kcContext;

  const { msg, msgStr, advancedMsg } = i18n;
  const appName = getAppName(realm);

  const [isFormSubmittable, setIsFormSubmittable] = useState(false);
  const [areTermsAccepted, setAreTermsAccepted] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);

  useLayoutEffect(() => {
    window.onSubmitRecaptcha = () => {
      formRef.current?.requestSubmit();
    };

    return () => {
      delete window.onSubmitRecaptcha;
    };
  }, []);

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        headerNode={
          messageHeader !== undefined ? (
            advancedMsg(messageHeader)
          ) : (
            <PageHeading>
              Register to <strong>{appName}</strong>
            </PageHeading>
          )
        }
        displayMessage={messagesPerField.exists('global')}
      >
        <div className={classes.content}>
          <form ref={formRef} className={classes.form} action={url.registrationAction} method="post">
            <UserProfileFormFields
              kcContext={kcContext}
              i18n={i18n}
              kcClsx={() => ''}
              onIsFormSubmittableValueChange={setIsFormSubmittable}
              doMakeUserConfirmPassword={doMakeUserConfirmPassword}
            />

            {termsAcceptanceRequired && (
              <TermsAcceptance
                i18n={i18n}
                messagesPerField={messagesPerField}
                areTermsAccepted={areTermsAccepted}
                onAreTermsAcceptedValueChange={setAreTermsAccepted}
              />
            )}

            {recaptchaRequired && (recaptchaVisible || recaptchaAction === undefined) && (
              <div
                className="g-recaptcha"
                data-size="compact"
                data-sitekey={recaptchaSiteKey}
                data-action={recaptchaAction}
              ></div>
            )}

            <div className={classes.formOptions}>
              <Link href={url.loginUrl}>{msg('backToLogin')}</Link>
            </div>

            {recaptchaRequired && !recaptchaVisible && recaptchaAction !== undefined ? (
              <Button
                className="g-recaptcha"
                data-sitekey={recaptchaSiteKey}
                data-callback="onSubmitRecaptcha"
                data-action={recaptchaAction}
                type="submit"
                kind="primary"
              >
                {msg('doRegister')}
              </Button>
            ) : (
              <Button
                type="submit"
                kind="primary"
                disabled={!isFormSubmittable || (termsAcceptanceRequired && !areTermsAccepted)}
              >
                {msgStr('doRegister')}
              </Button>
            )}
          </form>
        </div>
      </Template>
    </Layout>
  );
}

function TermsAcceptance(props: {
  i18n: I18n;
  messagesPerField: Pick<KcContext['messagesPerField'], 'existsError' | 'get'>;
  areTermsAccepted: boolean;
  onAreTermsAcceptedValueChange: (areTermsAccepted: boolean) => void;
}) {
  const { i18n, messagesPerField, areTermsAccepted, onAreTermsAcceptedValueChange } = props;

  const { msg } = i18n;

  return (
    <div className={classes.terms}>
      <div className={classes.termsTitle}>{msg('termsTitle')}</div>
      <div className={classes.termsText}>{msg('termsText')}</div>
      <Checkbox
        id="termsAccepted"
        name="termsAccepted"
        labelText={msg('acceptTerms')}
        checked={areTermsAccepted}
        onChange={(_, { checked }) => onAreTermsAcceptedValueChange(checked)}
        invalid={messagesPerField.existsError('termsAccepted')}
        invalidText={messagesPerField.existsError('termsAccepted') ? messagesPerField.get('termsAccepted') : undefined}
      />
    </div>
  );
}
