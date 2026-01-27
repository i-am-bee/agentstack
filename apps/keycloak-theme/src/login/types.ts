/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { KcContext } from "./KcContext";

export type LoginPageContext = Extract<KcContext, { pageId: "login.ftl" }>;
export type InfoMessage = NonNullable<LoginPageContext["message"]>;

export type Provider = NonNullable<
  NonNullable<LoginPageContext["social"]>["providers"]
>[number];

export type Realm = KcContext["realm"];
