/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { LoginView } from "../components/LoginView/LoginView";
import type { CustomPageProps } from "../types";

export type LoginProps = CustomPageProps<{ pageId: "login.ftl" }>;

export default function Login(props: LoginProps) {
  const { kcContext, i18n } = props;

  return (
    <LoginView
      kcContext={kcContext}
      i18n={i18n}
      withPassword
      withForgotPassword
      hiddenInputs={
        <input
          type="hidden"
          id="id-hidden-input"
          name="credentialId"
          value={kcContext.auth.selectedCredential}
        />
      }
    />
  );
}
