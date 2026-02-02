/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { LoginView } from "../components/LoginView/LoginView";
import type { CustomPageProps } from "../types";

export type LoginUsernameProps = CustomPageProps<{
  pageId: "login-username.ftl";
}>;

export default function LoginUsername(props: LoginUsernameProps) {
  const { kcContext, i18n } = props;

  return <LoginView kcContext={kcContext} i18n={i18n} />;
}
