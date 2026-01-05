/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

/*
 * For staging deployments, we force redirect to the "development" version of the docs.
 */
if (location.host.endsWith(".mintlify.app") && location.pathname.startsWith("/stable"))
    location.pathname = location.pathname.replace(/^\/stable/, "/development");