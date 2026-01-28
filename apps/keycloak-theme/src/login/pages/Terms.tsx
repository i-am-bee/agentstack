/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from "@carbon/react";
import type { PageProps } from "keycloakify/login/pages/PageProps";

import { Container } from "../components/Container/Container";
import { PageHeading } from "../components/PageHeading/PageHeading";
import type { I18n } from "../i18n";
import type { KcContext } from "../KcContext";
import classes from "./Terms.module.scss";

export default function Terms(
  props: PageProps<Extract<KcContext, { pageId: "terms.ftl" }>, I18n>,
) {
  const { kcContext, i18n, doUseDefaultCss, Template } = props;

  const { msg, msgStr } = i18n;

  const { url } = kcContext;

  return (
    <Container contentClassname={classes.root}>
      <Template
        kcContext={kcContext}
        i18n={i18n}
        doUseDefaultCss={doUseDefaultCss}
        displayMessage={false}
        headerNode={<PageHeading>Terms and Conditions</PageHeading>}
      >
        <div className={classes.content}>
          <div className={classes.termsText}>{msg("termsText")}</div>

          <form
            className={classes.actions}
            action={url.loginAction}
            method="POST"
          >
            <Button name="accept" id="kc-accept" type="submit" kind="primary">
              {msgStr("doAccept")}
            </Button>
            <Button
              name="cancel"
              id="kc-decline"
              type="submit"
              kind="secondary"
            >
              {msgStr("doDecline")}
            </Button>
          </form>
        </div>
      </Template>
    </Container>
  );
}
