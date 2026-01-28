/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from "clsx";
import type { ReactNode } from "react";

import classes from "./Container.module.scss";

interface ContainerProps {
  children: ReactNode;
  contentClassname?: string;
}

export function Container({ children, contentClassname }: ContainerProps) {
  return (
    <div className={classes.root}>
      <div className={classes.main}>
        <div className={clsx(classes.content, contentClassname)}>
          {children}
        </div>
      </div>
    </div>
  );
}
