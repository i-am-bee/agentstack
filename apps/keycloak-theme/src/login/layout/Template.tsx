/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Reset } from "@carbon/icons-react";
import { InlineNotification, TextInput } from "@carbon/react";
import { getKcClsx } from "keycloakify/login/lib/kcClsx";
import { useInitialize } from "keycloakify/login/Template.useInitialize";
import type { TemplateProps } from "keycloakify/login/TemplateProps";
import { clsx } from "keycloakify/tools/clsx";
import { useSetClassName } from "keycloakify/tools/useSetClassName";
import { useEffect, useId, useMemo } from "react";

import type { ContainerProps } from "../components/Container/Container";
import { Container } from "../components/Container/Container";
import type { I18n } from "../i18n";
import type { KcContext } from "../KcContext";
import { stripHtmlFromInfoMessage } from "../utils";
import classes from "./Template.module.scss";

interface Props extends TemplateProps<KcContext, I18n> {
  className?: string;
  centered?: boolean;
  size?: ContainerProps["size"];
}

export default function Template({
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
  centered = false,
  size,
  className,
  children,
}: Props) {
  const id = useId();
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
    <div
      className={clsx(
        kcClsx("kcLoginClass"),
        classes.root,
        { [classes.centered]: centered },
        className,
      )}
    >
      <Container size={size}>
        <div className={kcClsx("kcFormCardClass")}>
          <header className={kcClsx("kcFormHeaderClass")}>
            {(() => {
              const node = !(
                auth !== undefined &&
                auth.showUsername &&
                !auth.showResetCredentials
              ) ? (
                <h1 id="kc-page-title">{headerNode}</h1>
              ) : (
                <div
                  id="kc-username"
                  className={clsx(
                    kcClsx("kcFormGroupClass"),
                    classes.attemptedUsername,
                  )}
                >
                  <TextInput
                    id={`${id}-attempted-username`}
                    labelText={msgStr("usernameOrEmail")}
                    value={auth.attemptedUsername}
                    disabled
                  />
                  <a
                    id="reset-login"
                    href={url.loginRestartFlowUrl}
                    aria-label={msgStr("restartLoginTooltip")}
                    className={classes.restartLoginButton}
                  >
                    <Reset />
                    <span className="kc-tooltip-text">
                      {msg("restartLoginTooltip")}
                    </span>
                  </a>
                </div>
              );

              if (displayRequiredFields) {
                return (
                  <div className={kcClsx("kcContentWrapperClass")}>
                    <div
                      className={clsx(
                        kcClsx("kcLabelWrapperClass"),
                        "subtitle",
                      )}
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
      </Container>
    </div>
  );
}
