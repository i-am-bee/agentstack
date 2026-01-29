/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  Button,
  ButtonSet,
  InlineNotification,
  ListItem,
  UnorderedList,
} from "@carbon/react";

import { Layout } from "../components/Layout/Layout";
import Template from "../layout/Template";
import type { CustomPageProps } from "../types";
import classes from "./DeleteAccountConfirm.module.scss";

export default function DeleteAccountConfirm(
  props: CustomPageProps<{ pageId: "delete-account-confirm.ftl" }>,
) {
  const { kcContext, i18n, classes: kcClasses } = props;

  const { url, triggered_from_aia } = kcContext;

  const { msg, msgStr } = i18n;

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        classes={kcClasses}
        displayMessage={false}
        doUseDefaultCss={false}
        headerNode={msg("deleteAccountConfirm")}
        centered
      >
        <form action={url.loginAction} className={classes.form} method="post">
          <InlineNotification kind="warning" hideCloseButton lowContrast>
            {msg("irreversibleAction")}
          </InlineNotification>

          <div>
            <p>{msg("deletingImplies")}</p>
            <UnorderedList className={classes.list}>
              <ListItem>{msg("loggingOutImmediately")}</ListItem>
              <ListItem>{msg("errasingData")}</ListItem>
            </UnorderedList>

            <p className={classes.confirmation}>
              {msg("finalDeletionConfirmation")}
            </p>
          </div>

          <ButtonSet>
            <Button type="submit" kind="danger">
              {msgStr("doConfirmDelete")}
            </Button>
            {triggered_from_aia && (
              <Button
                type="submit"
                name="cancel-aia"
                value="true"
                kind="secondary"
              >
                {msgStr("doCancel")}
              </Button>
            )}
          </ButtonSet>
        </form>
      </Template>
    </Layout>
  );
}
