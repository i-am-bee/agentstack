/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowRight } from "@carbon/icons-react";
import { Button, Link, PasswordInput } from "@carbon/react";
import { kcSanitize } from "keycloakify/lib/kcSanitize";
import { useId, useState } from "react";

import { Layout } from "../components/Layout/Layout";
import { PageHeading } from "../components/PageHeading/PageHeading";
import { PasskeyLogin } from "../components/PasskeyLogin/PasskeyLogin";
import Template from "../layout/Template";
import type { CustomPageProps } from "../types";
import { getAppName } from "../utils";
import classes from "./LoginPassword.module.scss";

export type LoginPasswordProps = CustomPageProps<{
  pageId: "login-password.ftl";
}>;

export default function LoginPassword(props: LoginPasswordProps) {
  const id = useId();
  const { kcContext, i18n } = props;

  const { realm, url, messagesPerField } = kcContext;

  const { msg, msgStr } = i18n;

  const [isLoginButtonDisabled, setIsLoginButtonDisabled] = useState(false);

  const appName = getAppName(realm);
  const webAuthnButtonId = "authenticateWebAuthnButton";

  const hasError = messagesPerField.existsError("password");
  const errorMessage = hasError ? messagesPerField.get("password") : "";

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        headerNode={
          <PageHeading>
            Log in to <strong>{appName}</strong>
          </PageHeading>
        }
        displayMessage={!hasError}
      >
        <div className={classes.content}>
          <form
            className={classes.form}
            onSubmit={() => {
              setIsLoginButtonDisabled(true);
              return true;
            }}
            action={url.loginAction}
            method="post"
          >
            <PasswordInput
              id={`${id}-password`}
              name="password"
              labelText={msgStr("password")}
              autoFocus
              autoComplete="on"
              invalid={hasError}
              invalidText={
                hasError ? (
                  <span
                    dangerouslySetInnerHTML={{
                      __html: kcSanitize(errorMessage),
                    }}
                  />
                ) : undefined
              }
            />

            <div className={classes.options}>
              {realm.resetPasswordAllowed && (
                <Link href={url.loginResetCredentialsUrl}>
                  {msg("doForgotPassword")}
                </Link>
              )}
            </div>

            <Button
              type="submit"
              disabled={isLoginButtonDisabled}
              className={classes.submitButton}
              renderIcon={ArrowRight}
            >
              {msgStr("doLogIn")}
            </Button>
          </form>

          <PasskeyLogin
            kcContext={kcContext}
            i18n={i18n}
            webAuthnButtonId={webAuthnButtonId}
          />
        </div>
      </Template>
    </Layout>
  );
}
