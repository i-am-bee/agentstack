/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { APP_NAME } from "../constants";
import type { InfoMessage, Provider, Realm } from "./types";

export function isIbmProvider({
  alias,
  providerId,
  displayName,
}: Provider): boolean {
  return (
    providerId?.toLowerCase().includes("ibm") ||
    alias?.toLowerCase().includes("ibm") ||
    displayName?.toLowerCase().includes("ibm")
  );
}

export function stripHtmlFromInfoMessage(message: InfoMessage): InfoMessage {
  return {
    ...message,
    summary: message.summary
      .replace(/<br\s*\/?>/gi, "\n")
      .replace(/<\/?[^>]+(>|$)/g, ""),
  };
}

export function getAppName(realm: Realm): string {
  // Keycloak uses the realm name as a fallback if no display name is set, we dont want to show that
  const hasDisplayName = realm.displayName && realm.displayName !== realm.name;
  return hasDisplayName ? realm.displayName : APP_NAME;
}
