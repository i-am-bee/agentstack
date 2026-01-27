/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from "@carbon/react";
import type { PageProps } from "keycloakify/login/pages/PageProps";

import Bee from "../../svgs/bee.svg?react";
import { Container } from "../components/Container/Container";
import { LoginForm } from "../components/LoginForm/LoginForm";
import { PageHeading } from "../components/PageHeading/PageHeading";
import { PasskeyLogin } from "../components/PasskeyLogin/PasskeyLogin";
import type { I18n } from "../i18n";
import type { LoginPageContext } from "../types";
import { getAppName, isIbmProvider } from "../utils";
import classes from "./Login.module.scss";

export function Login(props: PageProps<LoginPageContext, I18n>) {
  const { kcContext, i18n, doUseDefaultCss, Template } = props;

  const { url, social, realm, registrationDisabled, messagesPerField } =
    kcContext;

  const providers = social?.providers ?? [];
  const appName = getAppName(realm);
  const webAuthnButtonId = "authenticateWebAuthnButton";

  const hasPasswordAuth = Boolean(realm.password);

  const { msg } = i18n;

  return (
    <Container>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={doUseDefaultCss}
        displayMessage={!messagesPerField.existsError("username", "password")}
        headerNode={
          <PageHeading>
            <>
              Log in to <strong>{appName}</strong>
            </>
          </PageHeading>
        }
        displayInfo={
          hasPasswordAuth && realm.registrationAllowed && !registrationDisabled
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
          {hasPasswordAuth && <LoginForm kcContext={kcContext} i18n={i18n} />}

          {hasPasswordAuth && providers.length !== 0 && (
            <hr className={classes.separator} />
          )}

          {providers.length !== 0 && (
            <div className={classes.providers}>
              {providers.map((provider) => {
                const { alias, displayName, loginUrl } = provider;
                return (
                  <Button
                    key={alias}
                    id={`social-${alias}`}
                    href={loginUrl}
                    kind="primary"
                    renderIcon={isIbmProvider(provider) ? Bee : undefined}
                  >
                    Continue with {displayName}
                  </Button>
                );
              })}
            </div>
          )}

          <PasskeyLogin
            kcContext={kcContext}
            i18n={i18n}
            webAuthnButtonId={webAuthnButtonId}
            doUseDefaultCss={doUseDefaultCss}
          />
        </div>
      </Template>
    </Container>
  );
}
