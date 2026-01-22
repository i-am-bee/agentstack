/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { InfoMessage, Provider } from "./types";

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
