/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Link } from "@carbon/react";

import { Layout } from "../components/Layout/Layout";
import { PageHeading } from "../components/PageHeading/PageHeading";
import Template from "../layout/Template";
import type { CustomPageProps } from "../types";
import classes from "./LoginVerifyEmail.module.scss";

export default function LoginVerifyEmail(
  props: CustomPageProps<{ pageId: "login-verify-email.ftl" }>,
) {
  const { kcContext, i18n } = props;

  const { msg } = i18n;

  const { url, user } = kcContext;

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        displayInfo
        headerNode={<PageHeading>{msg("emailVerifyTitle")}</PageHeading>}
        infoNode={
          <div className={classes.infoText}>
            {msg("emailVerifyInstruction2")}
            <br />
            <Link href={url.loginAction}>{msg("doClickHere")}</Link>{" "}
            {msg("emailVerifyInstruction3")}
          </div>
        }
        centered
      >
        <div className={classes.root}>
          <p>{msg("emailVerifyInstruction1", user?.email ?? "")}</p>
        </div>
      </Template>
    </Layout>
  );
}
