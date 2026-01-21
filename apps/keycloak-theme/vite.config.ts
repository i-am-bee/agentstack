/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { keycloakify } from "keycloakify/vite-plugin";
import path from "path";

export default defineConfig({
    plugins: [
        react(),
        keycloakify({
            accountThemeImplementation: "none",
            themeName: "agentstack-theme"
        })
    ],
    css: {
        preprocessorOptions: {
            scss: {
                api: "modern",
                // additionalData: `@use 'styles/common' as *; @use 'sass:math';`,
                quietDeps: true,
                includePaths: [
                    path.join(__dirname, "node_modules"),
                    path.join(__dirname, "src")
                ]
            }
        }
    }
});
