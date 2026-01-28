/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, Link, TextInput } from "@carbon/react";
import { kcSanitize } from "keycloakify/lib/kcSanitize";
import type { PageProps } from "keycloakify/login/pages/PageProps";

import { Container } from "../components/Container/Container";
import { PageHeading } from "../components/PageHeading/PageHeading";
import type { I18n } from "../i18n";
import type { KcContext } from "../KcContext";
import classes from "./LoginResetPassword.module.scss";

export default function LoginResetPassword(
  props: PageProps<
    Extract<KcContext, { pageId: "login-reset-password.ftl" }>,
    I18n
  >,
) {
  const { kcContext, i18n, doUseDefaultCss, Template } = props;

  const { url, realm, auth, messagesPerField } = kcContext;

  const { msg, msgStr } = i18n;

  const appName = realm.displayName || realm.name;

  const hasError = messagesPerField.existsError("username");
  const errorMessage = hasError ? messagesPerField.get("username") : "";

  return (
    <Container>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={doUseDefaultCss}
        displayInfo
        displayMessage={!hasError}
        infoNode={
          <div className={classes.info}>
            {realm.duplicateEmailsAllowed
              ? msg("emailInstructionUsername")
              : msg("emailInstruction")}
          </div>
        }
        headerNode={
          <PageHeading>
            <>
              Reset password for <strong>{appName}</strong>
            </>
          </PageHeading>
        }
      >
        <div className={classes.content}>
          <form
            id="kc-reset-password-form"
            className={classes.form}
            action={url.loginAction}
            method="post"
          >
            <TextInput
              id="username"
              name="username"
              labelText={
                !realm.loginWithEmailAllowed
                  ? msgStr("username")
                  : !realm.registrationEmailAsUsername
                    ? msgStr("usernameOrEmail")
                    : msgStr("email")
              }
              autoFocus
              defaultValue={auth.attemptedUsername ?? ""}
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

            <div className={classes.formOptions}>
              <Link href={url.loginUrl}>{msg("backToLogin")}</Link>
            </div>

            <Button type="submit" kind="primary">
              {msgStr("doSubmit")}
            </Button>
          </form>
        </div>
      </Template>
    </Container>
  );
}
