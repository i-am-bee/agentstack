/**
 * Copyright 2025 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { AppFooter, AppHeader } from "@i-am-bee/beeai-ui";
import { PropsWithChildren } from "react";
import classes from "./AppLayout.module.scss";
import { MainNav } from "../MainNav/MainNav";

export default function AppLayout({ children }: PropsWithChildren) {
  return (
    <div className={classes.root}>
      <AppHeader className={classes.header}>
        <MainNav />
      </AppHeader>
      <main className={classes.main}>{children}</main>
      <AppFooter className={classes.footer} />
    </div>
  );
}
