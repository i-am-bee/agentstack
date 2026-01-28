/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, Checkbox, Link } from "@carbon/react";
import type { PageProps } from "keycloakify/login/pages/PageProps";
import type { UserProfileFormFieldsProps } from "keycloakify/login/UserProfileFormFieldsProps";
import type { JSX } from "keycloakify/tools/JSX";
import type { LazyOrNot } from "keycloakify/tools/LazyOrNot";
import { useLayoutEffect, useRef, useState } from "react";

import { Container } from "../components/Container/Container";
import { PageHeading } from "../components/PageHeading/PageHeading";
import type { I18n } from "../i18n";
import type { KcContext } from "../KcContext";
import { getAppName } from "../utils";
import classes from "./Register.module.scss";

declare global {
  interface Window {
    onSubmitRecaptcha?: () => void;
  }
}

type RegisterProps = PageProps<
  Extract<KcContext, { pageId: "register.ftl" }>,
  I18n
> & {
  UserProfileFormFields: LazyOrNot<
    (props: UserProfileFormFieldsProps) => JSX.Element
  >;
  doMakeUserConfirmPassword: boolean;
};

export default function Register(props: RegisterProps) {
  const {
    kcContext,
    i18n,
    doUseDefaultCss,
    Template,
    UserProfileFormFields,
    doMakeUserConfirmPassword,
  } = props;

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
    <Container>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={doUseDefaultCss}
        headerNode={
          messageHeader !== undefined ? (
            advancedMsg(messageHeader)
          ) : (
            <PageHeading>
              <>
                Register to <strong>{appName}</strong>
              </>
            </PageHeading>
          )
        }
        displayMessage={messagesPerField.exists("global")}
      >
        <div className={classes.content}>
          <form
            ref={formRef}
            className={classes.form}
            action={url.registrationAction}
            method="post"
          >
            <UserProfileFormFields
              kcContext={kcContext}
              i18n={i18n}
              kcClsx={() => ""}
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

            {recaptchaRequired &&
              (recaptchaVisible || recaptchaAction === undefined) && (
                <div className={classes.recaptcha}>
                  <div
                    className="g-recaptcha"
                    data-size="compact"
                    data-sitekey={recaptchaSiteKey}
                    data-action={recaptchaAction}
                  ></div>
                </div>
              )}

            <div className={classes.formOptions}>
              <Link href={url.loginUrl}>{msg("backToLogin")}</Link>
            </div>

            {recaptchaRequired &&
            !recaptchaVisible &&
            recaptchaAction !== undefined ? (
              <Button
                className="g-recaptcha"
                data-sitekey={recaptchaSiteKey}
                data-callback="onSubmitRecaptcha"
                data-action={recaptchaAction}
                type="submit"
                kind="primary"
              >
                {msg("doRegister")}
              </Button>
            ) : (
              <Button
                type="submit"
                kind="primary"
                disabled={
                  !isFormSubmittable ||
                  (termsAcceptanceRequired && !areTermsAccepted)
                }
              >
                {msgStr("doRegister")}
              </Button>
            )}
          </form>
        </div>
      </Template>
    </Container>
  );
}

function TermsAcceptance(props: {
  i18n: I18n;
  messagesPerField: Pick<KcContext["messagesPerField"], "existsError" | "get">;
  areTermsAccepted: boolean;
  onAreTermsAcceptedValueChange: (areTermsAccepted: boolean) => void;
}) {
  const {
    i18n,
    messagesPerField,
    areTermsAccepted,
    onAreTermsAcceptedValueChange,
  } = props;

  const { msg } = i18n;

  return (
    <div className={classes.terms}>
      <div className={classes.termsTitle}>{msg("termsTitle")}</div>
      <div className={classes.termsText}>{msg("termsText")}</div>
      <Checkbox
        id="termsAccepted"
        name="termsAccepted"
        labelText={msg("acceptTerms")}
        checked={areTermsAccepted}
        onChange={(_, { checked }) => onAreTermsAcceptedValueChange(checked)}
        invalid={messagesPerField.existsError("termsAccepted")}
        invalidText={
          messagesPerField.existsError("termsAccepted")
            ? messagesPerField.get("termsAccepted")
            : undefined
        }
      />
    </div>
  );
}
