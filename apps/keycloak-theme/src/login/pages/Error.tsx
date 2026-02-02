/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from "@carbon/react";
import { kcSanitize } from "keycloakify/lib/kcSanitize";

import NotFound from "../../svgs/NotFound.svg?react";
import { Layout } from "../components/Layout/Layout";
import Template from "../layout/Template";
import type { CustomPageProps } from "../types";
import classes from "./Error.module.scss";

export default function Error(props: CustomPageProps<{ pageId: "error.ftl" }>) {
  const { kcContext, i18n, classes: kcClasses } = props;

  const { message, client, skipLink } = kcContext;

  const { msg } = i18n;

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        classes={kcClasses}
        displayMessage={false}
        headerNode=""
        centered
      >
        <div className={classes.root}>
          <NotFound className={classes.image} />
          <h1>{msg("errorTitle")}</h1>
          <p
            className={classes.message}
            dangerouslySetInnerHTML={{ __html: kcSanitize(message.summary) }}
          />
          {!skipLink &&
            client !== undefined &&
            client.baseUrl !== undefined && (
              <Button href={client.baseUrl}>{msg("backToApplication")}</Button>
            )}
        </div>
      </Template>
    </Layout>
  );
}
