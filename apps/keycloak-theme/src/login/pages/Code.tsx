/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { TextInput } from "@carbon/react";
import { kcSanitize } from "keycloakify/lib/kcSanitize";

import { Layout } from "../components/Layout/Layout";
import Template from "../layout/Template";
import type { CustomPageProps } from "../types";
import classes from "./Code.module.scss";

export default function Code(props: CustomPageProps<{ pageId: "code.ftl" }>) {
  const { kcContext, i18n, classes: kcClasses } = props;

  const { code } = kcContext;

  const { msg } = i18n;

  return (
    <Layout i18n={i18n}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={false}
        classes={kcClasses}
        displayMessage={false}
        headerNode={
          code.success
            ? msg("codeSuccessTitle")
            : msg("codeErrorTitle", code.error)
        }
        centered
      >
        <div className={classes.root}>
          {code.success ? (
            <>
              <p>{msg("copyCodeInstruction")}</p>
              <TextInput id="code" labelText="" value={code.code} readOnly />
            </>
          ) : (
            code.error && (
              <p
                dangerouslySetInnerHTML={{
                  __html: kcSanitize(code.error),
                }}
              />
            )
          )}
        </div>
      </Template>
    </Layout>
  );
}
