/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Link } from "@carbon/react";

import { Layout } from "../components/Layout/Layout";
import { PageHeading } from "../components/PageHeading/PageHeading";
import Template from "../layout/Template";
import type { CustomPageProps } from "../types";
import classes from "./LoginIdpLinkEmail.module.scss";

export default function LoginIdpLinkEmail(
  props: CustomPageProps<{ pageId: "login-idp-link-email.ftl" }>,
) {
  const { kcContext, i18n } = props;

  const { url, realm, brokerContext, idpAlias } = kcContext;

  const { msg } = i18n;

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        headerNode={
          <PageHeading>{msg("emailLinkIdpTitle", idpAlias)}</PageHeading>
        }
        centered
      >
        <div className={classes.root}>
          <p>
            {msg(
              "emailLinkIdp1",
              idpAlias,
              brokerContext.username,
              realm.displayName,
            )}
          </p>
          <p>
            {msg("emailLinkIdp2")}
            <br />
            <Link href={url.loginAction}>{msg("doClickHere")}</Link>{" "}
            {msg("emailLinkIdp3")}
          </p>
          <p>
            {msg("emailLinkIdp4")}
            <br />
            <Link href={url.loginAction}>{msg("doClickHere")}</Link>{" "}
            {msg("emailLinkIdp5")}
          </p>
        </div>
      </Template>
    </Layout>
  );
}
