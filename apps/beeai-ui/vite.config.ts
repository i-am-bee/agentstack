import { resolve } from 'node:path';
import { fileURLToPath, URL } from 'node:url';

import react from '@vitejs/plugin-react-swc';
import { defineConfig, loadEnv } from 'vite';
import svgr from 'vite-plugin-svgr';

import { getFeatureFlags } from '#utils/feature-flags.ts';

const phoenixServerTarget = 'http://localhost:6006';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const featureFlags = getFeatureFlags(env);

  return {
    plugins: [
      react(),
      svgr({
        include: '**/*.svg',
      }),
    ],
    define: {
      __APP_NAME__: JSON.stringify('BeeAI'),
      __PHOENIX_SERVER_TARGET__: JSON.stringify(phoenixServerTarget),
      __FEATURE_FLAGS__: JSON.stringify(featureFlags),
    },
    server: {
      proxy: {
        '/mcp': {
          target: 'http://localhost:8333',
        },
        '/api': {
          target: 'http://localhost:8333',
        },
        '/phoenix': {
          target: phoenixServerTarget,
        },
      },
    },
    resolve: {
      alias: {
        '~@ibm': resolve(__dirname, './node_modules/@ibm'),
      },
    },
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: `@use 'styles/common' as *; @use 'sass:math';`,
          silenceDeprecations: ['mixed-decls', 'global-builtin'],
          loadPaths: [fileURLToPath(new URL('src/', import.meta.url))],
        },
      },
      modules: {
        generateScopedName: '[name]_[local]_[hash:base64:5]',
      },
    },
  };
});
