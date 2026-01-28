/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from "@carbon/react";

import Bee from "../../svgs/bee.svg?react";
import { Layout } from "../components/Layout/Layout";
import { LoginForm } from "../components/LoginForm/LoginForm";
import { PageHeading } from "../components/PageHeading/PageHeading";
import { PasskeyLogin } from "../components/PasskeyLogin/PasskeyLogin";
import Template from "../layout/Template";
import type { CustomPageProps } from "../types";
import { getAppName, isIbmProvider } from "../utils";
import classes from "./Login.module.scss";

export type LoginProps = CustomPageProps<{ pageId: "login.ftl" }>;

export function Login(props: LoginProps) {
  const { kcContext, i18n } = props;

  const { url, social, realm, registrationDisabled, messagesPerField } =
    kcContext;

  const providers = social?.providers ?? [];
  const appName = getAppName(realm);
  const webAuthnButtonId = "authenticateWebAuthnButton";

  const hasPasswordAuth = Boolean(realm.password);

  const { msg } = i18n;

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
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
          />
        </div>
      </Template>
    </Layout>
  );
}
