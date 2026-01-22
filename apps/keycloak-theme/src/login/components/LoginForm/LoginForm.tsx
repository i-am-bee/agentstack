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
import { useState } from "react";

import type { I18n } from "../../i18n";
import type { KcContext } from "../../KcContext";
import styles from "./LoginForm.module.scss";

interface Props {
  kcContext: Extract<KcContext, { pageId: "login.ftl" }>;
  i18n: I18n;
}

export function LoginForm({ kcContext, i18n }: Props) {
  const { realm, url, usernameHidden, login, auth, messagesPerField } =
    kcContext;

  const { msg, msgStr } = i18n;
  const [isLoginButtonDisabled, setIsLoginButtonDisabled] = useState(false);

  const hasError = messagesPerField.existsError("username", "password");
  const errorMessage = hasError
    ? messagesPerField.getFirstError("username", "password")
    : "";

  return (
    <form
      className={styles.root}
      id="kc-form-login"
      onSubmit={() => {
        setIsLoginButtonDisabled(true);
        return true;
      }}
      action={url.loginAction}
      method="post"
    >
      {!usernameHidden && (
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

      <PasswordInput
        id="password"
        name="password"
        labelText={msgStr("password")}
        autoComplete="current-password"
        invalid={usernameHidden && hasError}
        invalidText={
          usernameHidden && hasError ? (
            <span
              dangerouslySetInnerHTML={{
                __html: kcSanitize(errorMessage),
              }}
            />
          ) : undefined
        }
      />

      <div className={styles.options}>
        {realm.rememberMe && !usernameHidden && (
          <Checkbox
            id="rememberMe"
            name="rememberMe"
            labelText={msgStr("rememberMe")}
            defaultChecked={!!login.rememberMe}
          />
        )}

        {realm.resetPasswordAllowed && (
          <Link href={url.loginResetCredentialsUrl}>
            {msg("doForgotPassword")}
          </Link>
        )}
      </div>

      <input
        type="hidden"
        id="id-hidden-input"
        name="credentialId"
        value={auth.selectedCredential}
      />

      <Button
        type="submit"
        disabled={isLoginButtonDisabled}
        className={styles.submitButton}
        renderIcon={ArrowRight}
      >
        {msgStr("doLogIn")}
      </Button>
    </form>
  );
}
