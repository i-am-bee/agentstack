/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { createGetKcContextMock } from "keycloakify/login/KcContext";
import type { DeepPartial } from "keycloakify/tools/DeepPartial";

import { kcEnvDefaults, themeNames } from "../kc.gen";
import type { KcContext } from "./KcContext";
import type {
  KcContextExtension,
  KcContextExtensionPerPage,
} from "./KcContext";
import KcPage from "./KcPage";

const kcContextExtension: KcContextExtension = {
  themeName: themeNames[0],
  properties: {
    ...kcEnvDefaults,
  },
};
const kcContextExtensionPerPage: KcContextExtensionPerPage = {};

export const { getKcContextMock } = createGetKcContextMock({
  kcContextExtension,
  kcContextExtensionPerPage,
  overrides: {},
  overridesPerPage: {},
});

export function createKcPageStory<PageId extends KcContext["pageId"]>(params: {
  pageId: PageId;
}) {
  const { pageId } = params;

  function KcPageStory(props: {
    kcContext?: DeepPartial<Extract<KcContext, { pageId: PageId }>>;
  }) {
    const { kcContext: overrides } = props;

    const kcContextMock = getKcContextMock({
      pageId,
      overrides,
    });

    return <KcPage kcContext={kcContextMock} />;
  }

  return { KcPageStory };
}
