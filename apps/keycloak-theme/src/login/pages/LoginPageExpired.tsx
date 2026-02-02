/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Link } from "@carbon/react";

import { Layout } from "../components/Layout/Layout";
import { PageHeading } from "../components/PageHeading/PageHeading";
import Template from "../layout/Template";
import type { CustomPageProps } from "../types";
import classes from "./LoginPageExpired.module.scss";

export default function LoginPageExpired(
  props: CustomPageProps<{ pageId: "login-page-expired.ftl" }>,
) {
  const { kcContext, i18n } = props;

  const { url } = kcContext;

  const { msg } = i18n;

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        headerNode={<PageHeading>{msg("pageExpiredTitle")}</PageHeading>}
        centered
      >
        <div className={classes.root}>
          <p>
            {msg("pageExpiredMsg1")}{" "}
            <Link id="loginRestartLink" href={url.loginRestartFlowUrl}>
              {msg("doClickHere")}
            </Link>
            .<br />
            {msg("pageExpiredMsg2")}{" "}
            <Link id="loginContinueLink" href={url.loginAction}>
              {msg("doClickHere")}
            </Link>
            .
          </p>
        </div>
      </Template>
    </Layout>
  );
}
