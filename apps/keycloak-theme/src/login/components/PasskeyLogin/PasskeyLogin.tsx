/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from "@carbon/react";

import type { I18n } from "../../i18n";
import type { LoginPageContext } from "../../types";

type Props = {
  kcContext: Extract<LoginPageContext, { pageId: "login.ftl" }>;
  i18n: I18n;
  webAuthnButtonId: string;
  doUseDefaultCss?: boolean;
};

export function PasskeyLogin(props: Props) {
  const { kcContext, i18n, webAuthnButtonId } = props;

  const { url, enableWebAuthnConditionalUI, authenticators } = kcContext;
  const { msgStr } = i18n;

  if (!enableWebAuthnConditionalUI) {
    return null;
  }

  return (
    <>
      <form id="webauth" action={url.loginAction} method="post">
        <input type="hidden" id="clientDataJSON" name="clientDataJSON" />
        <input type="hidden" id="authenticatorData" name="authenticatorData" />
        <input type="hidden" id="signature" name="signature" />
        <input type="hidden" id="credentialId" name="credentialId" />
        <input type="hidden" id="userHandle" name="userHandle" />
        <input type="hidden" id="error" name="error" />
      </form>

      {authenticators !== undefined &&
        authenticators.authenticators.length !== 0 && (
          <form id="authn_select">
            {authenticators.authenticators.map((authenticator, i) => (
              <input
                key={i}
                type="hidden"
                name="authn_use_chk"
                readOnly
                value={authenticator.credentialId}
              />
            ))}
          </form>
        )}

      <Button id={webAuthnButtonId} type="button" kind="secondary">
        {msgStr("passkey-doAuthenticate")}
      </Button>
    </>
  );
}
