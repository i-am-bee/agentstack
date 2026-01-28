/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import "../styles/style.scss";

import type { ClassKey } from "keycloakify/login";
import DefaultPage from "keycloakify/login/DefaultPage";
import { lazy, Suspense } from "react";

import { useI18n } from "../login/i18n";
import type { KcContext } from "../login/KcContext";
import { useDarkModeScript } from "./hooks/useDarkModeScript";
import Template from "./layout/Template";
import { Login } from "./pages/Login";
import Register from "./pages/Register";
import Terms from "./pages/Terms";

const UserProfileFormFields = lazy(
  () => import("./components/UserProfileForm/UserProfileFormFields"),
);
const LoginResetPassword = lazy(() => import("./pages/LoginResetPassword"));

const doMakeUserConfirmPassword = true;

export default function KcPage(props: { kcContext: KcContext }) {
  const { kcContext } = props;

  const { i18n } = useI18n({ kcContext });

  useDarkModeScript();

  return (
    <Suspense>
      {(() => {
        switch (kcContext.pageId) {
          case "login.ftl":
            return (
              <Login
                kcContext={kcContext}
                i18n={i18n}
                Template={Template}
                doUseDefaultCss={false}
              />
            );
          case "register.ftl":
            return (
              <Register
                {...{ kcContext, i18n, classes }}
                Template={Template}
                doUseDefaultCss={false}
                UserProfileFormFields={UserProfileFormFields}
                doMakeUserConfirmPassword={doMakeUserConfirmPassword}
              />
            );
          case "terms.ftl":
            return (
              <Terms
                {...{ kcContext, i18n, classes }}
                Template={Template}
                doUseDefaultCss={false}
              />
            );
          case "login-reset-password.ftl":
            return (
              <LoginResetPassword
                {...{ kcContext, i18n, classes }}
                Template={Template}
                doUseDefaultCss={false}
              />
            );
          default:
            return (
              <DefaultPage
                kcContext={kcContext}
                i18n={i18n}
                classes={classes}
                Template={Template}
                doUseDefaultCss={true}
                UserProfileFormFields={UserProfileFormFields}
                doMakeUserConfirmPassword={doMakeUserConfirmPassword}
              />
            );
        }
      })()}
    </Suspense>
  );
}

const classes = {} satisfies { [key in ClassKey]?: string };
