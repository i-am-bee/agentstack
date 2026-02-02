/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, ButtonSet } from "@carbon/react";

import { Layout } from "../components/Layout/Layout";
import { PageHeading } from "../components/PageHeading/PageHeading";
import Template from "../layout/Template";
import type { CustomPageProps } from "../types";
import classes from "./DeleteCredential.module.scss";

export default function DeleteCredential(
  props: CustomPageProps<{ pageId: "delete-credential.ftl" }>,
) {
  const { kcContext, i18n } = props;

  const { msgStr, msg } = i18n;

  const { url, credentialLabel } = kcContext;

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        displayMessage={false}
        headerNode={
          <PageHeading>
            {msg("deleteCredentialTitle", credentialLabel)}
          </PageHeading>
        }
        centered
      >
        <div className={classes.content}>
          <div>{msg("deleteCredentialMessage", credentialLabel)}</div>

          <form className={classes.form} action={url.loginAction} method="POST">
            <ButtonSet>
              <Button type="submit" kind="danger" name="accept" id="kc-accept">
                {msgStr("doConfirmDelete")}
              </Button>
              <Button
                type="submit"
                kind="secondary"
                name="cancel-aia"
                id="kc-decline"
              >
                {msgStr("doCancel")}
              </Button>
            </ButtonSet>
          </form>
        </div>
      </Template>
    </Layout>
  );
}
