/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from "@carbon/react";

import type { Provider } from "../../types";
import classes from "./SocialProviders.module.scss";

interface SocialProvidersProps {
  providers: Provider[];
}

export function SocialProviders({ providers }: SocialProvidersProps) {
  if (providers.length === 0) {
    return null;
  }

  return (
    <div className={classes.root}>
      {providers.map((provider) => {
        const { alias, displayName, loginUrl } = provider;
        return (
          <Button
            key={alias}
            id={`social-${alias}`}
            href={loginUrl}
            kind="primary"
          >
            Continue with {displayName}
          </Button>
        );
      })}
    </div>
  );
}
