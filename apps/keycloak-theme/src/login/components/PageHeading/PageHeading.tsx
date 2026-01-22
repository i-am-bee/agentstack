/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ReactNode } from "react";

import classes from "./PageHeading.module.scss";

type PageHeadingProps = {
  children: ReactNode;
};

export function PageHeading({ children }: PageHeadingProps) {
  return <h1 className={classes.heading}>{children}</h1>;
}
