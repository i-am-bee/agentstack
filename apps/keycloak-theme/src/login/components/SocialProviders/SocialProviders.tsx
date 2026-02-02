/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from "@carbon/react";
import clsx from "clsx";

import type { Provider } from "../../types";
import classes from "./SocialProviders.module.scss";

interface SocialProvidersProps {
  providers: Provider[];
  isSsoOnly?: boolean;
}

export function SocialProviders({
  providers,
  isSsoOnly,
}: SocialProvidersProps) {
  if (providers.length === 0) {
    return null;
  }

  return (
    <ul className={clsx(classes.root, { [classes.ssoOnly]: isSsoOnly })}>
      {providers.map((provider) => {
        const { alias, displayName, loginUrl } = provider;
        return (
          <li key={alias}>
            <Button
              id={`social-${alias}`}
              href={loginUrl}
              kind={isSsoOnly ? "secondary" : "primary"}
            >
              Login with {displayName}
            </Button>
          </li>
        );
      })}
    </ul>
  );
}
