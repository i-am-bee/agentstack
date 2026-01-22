/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { InlineNotification } from "@carbon/react";
import { getKcClsx } from "keycloakify/login/lib/kcClsx";
import { useInitialize } from "keycloakify/login/Template.useInitialize";
import type { TemplateProps } from "keycloakify/login/TemplateProps";
import { clsx } from "keycloakify/tools/clsx";
import { useSetClassName } from "keycloakify/tools/useSetClassName";
import { useEffect, useMemo } from "react";

import { LocaleNav } from "../components/LocaleNav/LocaleNav";
import type { I18n } from "../i18n";
import type { KcContext } from "../KcContext";
import { stripHtmlFromInfoMessage } from "../utils";
import classes from "./Template.module.scss";

export default function Template(props: TemplateProps<KcContext, I18n>) {
  const {
    displayInfo = false,
    displayMessage = true,
    displayRequiredFields = false,
    headerNode,
    socialProvidersNode = null,
    infoNode = null,
    documentTitle,
    bodyClassName,
    kcContext,
    i18n,
    doUseDefaultCss,
    classes: kcClasses,
    children,
  } = props;

  const { kcClsx } = getKcClsx({ doUseDefaultCss, classes: kcClasses });
  const { msg, msgStr } = i18n;

  const {
    realm,
    auth,
    url,
    message: origMessage,
    isAppInitiatedAction,
  } = kcContext;

  const message = useMemo(
    () => (origMessage ? stripHtmlFromInfoMessage(origMessage) : undefined),
    [origMessage],
  );

  useEffect(() => {
    document.title =
      documentTitle ?? msgStr("loginTitle", realm.displayName || realm.name);
  }, []);

  useSetClassName({
    qualifiedName: "html",
    className: kcClsx("kcHtmlClass"),
  });

  useSetClassName({
    qualifiedName: "body",
    className: bodyClassName ?? kcClsx("kcBodyClass"),
  });

  const { isReadyToRender } = useInitialize({ kcContext, doUseDefaultCss });

  if (!isReadyToRender) {
    return null;
  }

  return (
    <div className={clsx(kcClsx("kcLoginClass"), classes.root)}>
      <div className={kcClsx("kcFormCardClass")}>
        <header className={kcClsx("kcFormHeaderClass")}>
          <LocaleNav i18n={i18n} />

          {(() => {
            const node = !(
              auth !== undefined &&
              auth.showUsername &&
              !auth.showResetCredentials
            ) ? (
              <h1 id="kc-page-title">{headerNode}</h1>
            ) : (
              <div id="kc-username" className={kcClsx("kcFormGroupClass")}>
                <label id="kc-attempted-username">
                  {auth.attemptedUsername}
                </label>
                <a
                  id="reset-login"
                  href={url.loginRestartFlowUrl}
                  aria-label={msgStr("restartLoginTooltip")}
                >
                  <div className="kc-login-tooltip">
                    <i className={kcClsx("kcResetFlowIcon")}></i>
                    <span className="kc-tooltip-text">
                      {msg("restartLoginTooltip")}
                    </span>
                  </div>
                </a>
              </div>
            );

            if (displayRequiredFields) {
              return (
                <div className={kcClsx("kcContentWrapperClass")}>
                  <div
                    className={clsx(kcClsx("kcLabelWrapperClass"), "subtitle")}
                  >
                    <span className="subtitle">
                      <span className="required">*</span>
                      {msg("requiredFields")}
                    </span>
                  </div>
                  <div className="col-md-10">{node}</div>
                </div>
              );
            }

            return node;
          })()}
        </header>

        <div>
          <div>
            {/* App-initiated actions should not see warning messages about the need to complete the action during login. */}
            {displayMessage &&
              message !== undefined &&
              (message.type !== "warning" || !isAppInitiatedAction) && (
                <InlineNotification
                  kind={message.type === "error" ? "error" : message.type}
                  lowContrast
                  hideCloseButton
                  title=""
                  subtitle={message.summary}
                  className={classes.notification}
                />
              )}
            {children}
            {auth !== undefined && auth.showTryAnotherWayLink && (
              <form
                id="kc-select-try-another-way-form"
                action={url.loginAction}
                method="post"
              >
                <div className={kcClsx("kcFormGroupClass")}>
                  <input type="hidden" name="tryAnotherWay" value="on" />
                  <a
                    href="#"
                    id="try-another-way"
                    onClick={(event) => {
                      document.forms[
                        "kc-select-try-another-way-form" as never
                      ].requestSubmit();
                      event.preventDefault();
                      return false;
                    }}
                  >
                    {msg("doTryAnotherWay")}
                  </a>
                </div>
              </form>
            )}
            {socialProvidersNode}
            {displayInfo && infoNode && (
              <div className={classes.infoBox}>{infoNode}</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
