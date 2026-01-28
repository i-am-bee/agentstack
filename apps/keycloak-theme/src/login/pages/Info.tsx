/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from "@carbon/react";
import { kcSanitize } from "keycloakify/lib/kcSanitize";

import { Layout } from "../components/Layout/Layout";
import Template from "../layout/Template";
import type { CustomPageProps } from "../types";
import classes from "./Info.module.scss";

export default function Info(props: CustomPageProps<{ pageId: "info.ftl" }>) {
  const { kcContext, i18n, classes: kcClasses } = props;

  const { advancedMsgStr, msg } = i18n;

  const {
    messageHeader,
    message,
    requiredActions,
    skipLink,
    pageRedirectUri,
    actionUri,
    client,
  } = kcContext;

  const messageHtml = (() => {
    let html = message.summary?.trim();

    if (requiredActions) {
      html += " <b>";

      html += requiredActions
        .map((requiredAction) =>
          advancedMsgStr(`requiredAction.${requiredAction}`),
        )
        .join(", ");

      html += "</b>";
    }

    return html;
  })();

  const backLink = (() => {
    if (skipLink) {
      return null;
    }

    if (pageRedirectUri) {
      return { href: pageRedirectUri, label: msg("backToApplication") };
    }
    if (actionUri) {
      return { href: actionUri, label: msg("proceedWithAction") };
    }

    if (client.baseUrl) {
      return { href: client.baseUrl, label: msg("backToApplication") };
    }

    return null;
  })();

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        classes={kcClasses}
        displayMessage={false}
        doUseDefaultCss={false}
        headerNode={
          <span
            dangerouslySetInnerHTML={{
              __html: kcSanitize(
                messageHeader ? advancedMsgStr(messageHeader) : message.summary,
              ),
            }}
          />
        }
        centered
      >
        <div className={classes.root}>
          <p
            className={classes.message}
            dangerouslySetInnerHTML={{ __html: kcSanitize(messageHtml) }}
          />
          {backLink && <Button href={backLink.href}>{backLink.label}</Button>}
        </div>
      </Template>
    </Layout>
  );
}
