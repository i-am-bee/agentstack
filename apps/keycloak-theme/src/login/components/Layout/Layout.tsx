/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from "clsx";
import type { ReactNode } from "react";

import type { I18n } from "../../i18n";
import classes from "./Layout.module.scss";

interface LayoutProps {
  children: ReactNode;
  contentClassname?: string;
  i18n: I18n;
}

export function Layout({ children, contentClassname /*, i18n*/ }: LayoutProps) {
  return (
    <div className={classes.root}>
      <div className={classes.header}>
        {/* Uncomment if Localization is needed */}
        {/* <LocaleNav i18n={i18n} /> */}
      </div>
      <div className={classes.main}>
        <div className={clsx(classes.content, contentClassname)}>
          {children}
        </div>
      </div>
    </div>
  );
}
