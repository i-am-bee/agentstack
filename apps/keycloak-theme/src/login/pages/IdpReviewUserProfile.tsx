/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowRight } from "@carbon/icons-react";
import { Button } from "@carbon/react";
import type { UserProfileFormFieldsProps } from "keycloakify/login/UserProfileFormFieldsProps";
import type { JSX } from "keycloakify/tools/JSX";
import type { LazyOrNot } from "keycloakify/tools/LazyOrNot";
import { useState } from "react";

import { Layout } from "../components/Layout/Layout";
import Template from "../layout/Template";
import type { CustomPageProps } from "../types";
import classes from "./IdpReviewUserProfile.module.scss";

type IdpReviewUserProfileProps = CustomPageProps<{
  pageId: "idp-review-user-profile.ftl";
}> & {
  UserProfileFormFields: LazyOrNot<
    (props: UserProfileFormFieldsProps) => JSX.Element
  >;
  doMakeUserConfirmPassword: boolean;
};

export default function IdpReviewUserProfile(props: IdpReviewUserProfileProps) {
  const { kcContext, i18n, UserProfileFormFields, doMakeUserConfirmPassword } =
    props;

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

            <Button
              type="submit"
              kind="primary"
              disabled={!isFormSubmittable}
              renderIcon={ArrowRight}
              className={classes.submitButton}
            >
              {msgStr("doSubmit")}
            </Button>
          </form>
        </div>
      </Template>
    </Layout>
  );
}
