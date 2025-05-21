import { resolve } from 'node:path';
import { fileURLToPath, URL } from 'node:url';

import react from '@vitejs/plugin-react-swc';
import { defineConfig, loadEnv } from 'vite';
import svgr from 'vite-plugin-svgr';

import { featureFlagsSchema } from '#utils/feature-flags.ts';

const phoenixServerTarget = 'http://localhost:6006';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  const featureFlags = featureFlagsSchema.safeParse(
    (() => {
      try {
        return JSON.parse(env.VITE_FEATURE_FLAGS ?? '{}');
      } catch (error) {
        console.error('\n❌  Failed to parse JSON for VITE_FEATURE_FLAGS\n');
        throw error;
      }
    })(),
  );

  if (!featureFlags.success) {
    console.error('\n❌  Invalid VITE_FEATURE_FLAGS\n', featureFlags.error.format(), '\n');
    throw featureFlags.error;
  }

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
      __FEATURE_FLAGS__: JSON.stringify(featureFlags.data),
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
