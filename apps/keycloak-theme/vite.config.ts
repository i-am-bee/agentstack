/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import react from "@vitejs/plugin-react";
import { keycloakify } from "keycloakify/vite-plugin";
import path from "path";
import { defineConfig } from "vite";
import { viteStaticCopy } from "vite-plugin-static-copy";
import svgr from "vite-plugin-svgr";

export default defineConfig({
  define: {
    "import.meta.env.VITE_APP_NAME": JSON.stringify(
      process.env.APP_NAME || "Agent Stack",
    ),
  },
  plugins: [
    react(),
    svgr(),
    viteStaticCopy({
      targets: [
        {
          src: path.join(
            __dirname,
            "node_modules/@ibm/plex/IBM-Plex-Sans/fonts/split/woff2/*.woff2",
          ),
          dest: "assets/~@ibm/plex/IBM-Plex-Sans/fonts/split/woff2",
        },
      ],
    }),
    keycloakify({
      accountThemeImplementation: "none",
      themeName: "agentstack",
    }),
  ],
  css: {
    modules: {
      generateScopedName: "[name]__[local]__[hash:base64:5]",
    },
    preprocessorOptions: {
      scss: {
        api: "modern",
        quietDeps: true,
        additionalData: `@use 'styles/common' as *; @use 'sass:math';`,
        includePaths: [
          path.join(__dirname, "node_modules"),
          path.join(__dirname, "src"),
          path.join(__dirname, "../agentstack-ui/src"),
        ],
        loadPaths: [path.join(__dirname, "../agentstack-ui/src")],
      },
    },
  },
  resolve: {
    alias: {
      styles: path.resolve(__dirname, "../agentstack-ui/src/styles"),
    },
  },
});
