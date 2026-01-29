/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PageProps } from "keycloakify/login/pages/PageProps";

import type { I18n } from "./i18n";
import type { KcContext } from "./KcContext";
import type { LoginProps } from "./pages/Login";
import type { LoginPasswordProps } from "./pages/LoginPassword";
import type { LoginUsernameProps } from "./pages/LoginUsername";

export type LoginUsernameContext = LoginUsernameProps["kcContext"];
export type LoginPasswordContext = LoginPasswordProps["kcContext"];
export type LoginPageContext = LoginProps["kcContext"];
export type InfoMessage = NonNullable<LoginPageContext["message"]>;

export type Provider = NonNullable<
  NonNullable<LoginPageContext["social"]>["providers"]
>[number];

export type Realm = KcContext["realm"];

export type CustomPageProps<T extends { pageId: KcContext["pageId"] }> = Omit<
  PageProps<Extract<KcContext, T>, I18n>,
  "Template" | "doUseDefaultCss"
>;

export interface UserProfileFormPageProps {
  doMakeUserConfirmPassword: boolean;
}
