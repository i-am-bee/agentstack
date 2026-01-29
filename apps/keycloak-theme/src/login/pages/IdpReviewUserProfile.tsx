/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from "@carbon/react";
import { useState } from "react";

import { Layout } from "../components/Layout/Layout";
import Template from "../layout/Template";
import type { CustomPageProps, UserProfileFormPageProps } from "../types";
import UserProfileFormFields from "../UserProfileFormFields";
import classes from "./IdpReviewUserProfile.module.scss";

type IdpReviewUserProfileProps = CustomPageProps<{
  pageId: "idp-review-user-profile.ftl";
}> &
  UserProfileFormPageProps;

export default function IdpReviewUserProfile(props: IdpReviewUserProfileProps) {
  const { kcContext, i18n, doMakeUserConfirmPassword } = props;

  const { msg, msgStr } = i18n;

  const { url, messagesPerField } = kcContext;

  const [isFormSubmittable, setIsFormSubmittable] = useState(false);

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        displayMessage={messagesPerField.exists("global")}
        headerNode={msg("loginIdpReviewProfileTitle")}
      >
        <div className={classes.content}>
          <form className={classes.form} action={url.loginAction} method="post">
            <UserProfileFormFields
              kcContext={kcContext}
              i18n={i18n}
              kcClsx={() => ""}
              onIsFormSubmittableValueChange={setIsFormSubmittable}
              doMakeUserConfirmPassword={doMakeUserConfirmPassword}
            />

            <Button type="submit" kind="primary" disabled={!isFormSubmittable}>
              {msgStr("doSubmit")}
            </Button>
          </form>
        </div>
      </Template>
    </Layout>
  );
}
