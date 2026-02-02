/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowRight } from "@carbon/icons-react";
import {
  Button,
  Checkbox,
  Link,
  PasswordInput,
  TextInput,
} from "@carbon/react";
import { kcSanitize } from "keycloakify/lib/kcSanitize";
import type { ReactNode } from "react";
import { useId, useState } from "react";

import type { I18n } from "../../i18n";
import type { KcContext } from "../../KcContext";
import Template from "../../layout/Template";
import { getAppName, isSsoOnlyTheme } from "../../utils";
import { Layout } from "../Layout/Layout";
import { PageHeading } from "../PageHeading/PageHeading";
import { PasskeyLogin } from "../PasskeyLogin/PasskeyLogin";
import { Separator } from "../Separator/Separator";
import { SocialProviders } from "../SocialProviders/SocialProviders";
import classes from "./LoginView.module.scss";

type LoginContext = Extract<
  KcContext,
  { pageId: "login.ftl" | "login-username.ftl" }
>;

interface LoginPageProps {
  kcContext: LoginContext;
  i18n: I18n;
  withPassword?: boolean;
  withForgotPassword?: boolean;
  formOptions?: ReactNode;
  hiddenInputs?: ReactNode;
}

export function LoginView({
  kcContext,
  i18n,
  withPassword = false,
  withForgotPassword = false,
  formOptions,
  hiddenInputs,
}: LoginPageProps) {
  const id = useId();

  const {
    social,
    realm,
    url,
    usernameHidden,
    login,
    registrationDisabled,
    messagesPerField,
    themeName,
  } = kcContext;

  const { msg, msgStr } = i18n;
  const [isLoginButtonDisabled, setIsLoginButtonDisabled] = useState(false);

  const appName = getAppName(realm);
  const webAuthnButtonId = "authenticateWebAuthnButton";
  const providers = social?.providers ?? [];
  const isSsoOnly = !realm.password || isSsoOnlyTheme(themeName);

  const hasError = withPassword
    ? messagesPerField.existsError("username", "password")
    : messagesPerField.existsError("username");
  const errorMessage = hasError
    ? withPassword
      ? messagesPerField.getFirstError("username", "password")
      : messagesPerField.getFirstError("username")
    : "";

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        displayMessage={!hasError}
        headerNode={
          <PageHeading>
            Log in to <strong>{appName}</strong>
          </PageHeading>
        }
        displayInfo={
          !isSsoOnly && realm.registrationAllowed && !registrationDisabled
        }
        infoNode={
          <div className={classes.registration}>
            <span>
              {msg("noAccount")}{" "}
              <a href={url.registrationUrl}>{msg("doRegister")}</a>
            </span>
          </div>
        }
      >
        <div className={classes.content}>
          {!isSsoOnly && (
            <form
              className={classes.form}
              onSubmit={() => {
                setIsLoginButtonDisabled(true);
                return true;
              }}
              action={url.loginAction}
              method="post"
            >
              {!usernameHidden && (
                <TextInput
                  id={`${id}-username`}
                  name="username"
                  labelText={
                    !realm.loginWithEmailAllowed
                      ? msgStr("username")
                      : !realm.registrationEmailAsUsername
                        ? msgStr("usernameOrEmail")
                        : msgStr("email")
                  }
                  defaultValue={login.username ?? ""}
                  autoFocus
                  autoComplete="username"
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
              )}

              {withPassword && (
                <PasswordInput
                  id={`${id}-password`}
                  name="password"
                  labelText={msgStr("password")}
                  autoComplete="current-password"
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
              )}

              <div className={classes.options}>
                {realm.rememberMe && !usernameHidden && (
                  <Checkbox
                    id={`${id}-rememberMe`}
                    name="rememberMe"
                    labelText={msgStr("rememberMe")}
                    defaultChecked={Boolean(login.rememberMe)}
                  />
                )}

                {withForgotPassword && realm.resetPasswordAllowed && (
                  <Link href={url.loginResetCredentialsUrl}>
                    {msg("doForgotPassword")}
                  </Link>
                )}

                {formOptions}
              </div>

              {hiddenInputs}

              <Button
                type="submit"
                disabled={isLoginButtonDisabled}
                className={classes.submitButton}
                renderIcon={ArrowRight}
              >
                {msgStr("doLogIn")}
              </Button>
            </form>
          )}

          {!isSsoOnly && providers.length !== 0 && <Separator text="OR" />}

          <SocialProviders providers={providers} isSsoOnly={isSsoOnly} />

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
