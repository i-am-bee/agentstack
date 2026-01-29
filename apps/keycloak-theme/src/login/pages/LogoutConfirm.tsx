/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, Link } from "@carbon/react";

import { Layout } from "../components/Layout/Layout";
import { PageHeading } from "../components/PageHeading/PageHeading";
import Template from "../layout/Template";
import type { CustomPageProps } from "../types";
import classes from "./LogoutConfirm.module.scss";

export default function LogoutConfirm(
  props: CustomPageProps<{ pageId: "logout-confirm.ftl" }>,
) {
  const { kcContext, i18n } = props;
  const { url, client, logoutConfirm } = kcContext;
  const { msg } = i18n;

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        headerNode={<PageHeading>{msg("logoutConfirmTitle")}</PageHeading>}
        centered
      >
        <div className={classes.content}>
          <p className={classes.infoText}>{msg("logoutConfirmHeader")}</p>
          <form
            className={classes.form}
            action={url.logoutConfirmAction}
            method="POST"
          >
            <input
              type="hidden"
              name="session_code"
              value={logoutConfirm.code}
            />
            <Button type="submit" name="confirmLogout">
              {msg("doLogout")}
            </Button>
          </form>
          {!logoutConfirm.skipLink && client.baseUrl && (
            <div className={classes.backLink}>
              <Link href={client.baseUrl}>{msg("backToApplication")}</Link>
            </div>
          )}
        </div>
      </Template>
    </Layout>
  );
}
