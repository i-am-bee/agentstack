/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from "@carbon/react";
import { useState } from "react";

import { Layout } from "../components/Layout/Layout";
import { PageHeading } from "../components/PageHeading/PageHeading";
import Template from "../layout/Template";
import type { CustomPageProps, UserProfileFormPageProps } from "../types";
import UserProfileFormFields from "../UserProfileFormFields";
import classes from "./LoginUpdateProfile.module.scss";

export default function LoginUpdateProfile(
  props: CustomPageProps<{
    pageId: "login-update-profile.ftl";
  }> &
    UserProfileFormPageProps,
) {
  const { kcContext, i18n, doMakeUserConfirmPassword } = props;

  const { messagesPerField, url, isAppInitiatedAction } = kcContext;

  const { msg, msgStr } = i18n;

  const [isFormSubmittable, setIsFormSubmittable] = useState(false);

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        headerNode={<PageHeading>{msg("loginProfileTitle")}</PageHeading>}
        displayMessage={messagesPerField.exists("global")}
      >
        <div className={classes.content}>
          <form
            id="kc-update-profile-form"
            className={classes.form}
            action={url.loginAction}
            method="post"
          >
            <UserProfileFormFields
              kcContext={kcContext}
              i18n={i18n}
              kcClsx={() => ""}
              onIsFormSubmittableValueChange={setIsFormSubmittable}
              doMakeUserConfirmPassword={doMakeUserConfirmPassword}
            />

            <div className={classes.actions}>
              <Button
                type="submit"
                kind="primary"
                disabled={!isFormSubmittable}
              >
                {msgStr("doSubmit")}
              </Button>
              {isAppInitiatedAction && (
                <Button
                  type="submit"
                  kind="secondary"
                  name="cancel-aia"
                  value="true"
                >
                  {msg("doCancel")}
                </Button>
              )}
            </div>
          </form>
        </div>
      </Template>
    </Layout>
  );
}
