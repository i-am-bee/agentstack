/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, ButtonSet } from "@carbon/react";

import { Layout } from "../components/Layout/Layout";
import { PageHeading } from "../components/PageHeading/PageHeading";
import Template from "../layout/Template";
import type { CustomPageProps } from "../types";
import classes from "./LinkIdpAction.module.scss";

export default function LinkIdpAction(
  props: CustomPageProps<{ pageId: "link-idp-action.ftl" }>,
) {
  const { kcContext, i18n } = props;
  const { idpDisplayName, url } = kcContext;
  const { msg } = i18n;

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        headerNode={
          <PageHeading>{msg("linkIdpActionTitle", idpDisplayName)}</PageHeading>
        }
        displayMessage={false}
        centered
      >
        <div className={classes.content}>
          <p className={classes.message}>
            {msg("linkIdpActionMessage", idpDisplayName)}
          </p>
          <form className={classes.form} action={url.loginAction} method="post">
            <ButtonSet>
              <Button type="submit" name="continue">
                {msg("doContinue")}
              </Button>
              <Button kind="secondary" type="submit" name="cancel-aia">
                {msg("doCancel")}
              </Button>
            </ButtonSet>
          </form>
        </div>
      </Template>
    </Layout>
  );
}
