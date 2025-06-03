import { resolve } from 'node:path';
import { fileURLToPath, URL } from 'node:url';

import react from '@vitejs/plugin-react-swc';
import { defineConfig, loadEnv, type UserConfig } from 'vite';
import svgr from 'vite-plugin-svgr';

const DEFAULT_ENV = {
  VITE_APP_NAME: 'BeeAI',
  VITE_APP_FAVICON_SVG: '/bee.svg',
  API_SERVER_TARGET: 'http://127.0.0.1:8333',
  PHOENIX_SERVER_TARGET: 'http://localhost:6006',
} as const;

export default defineConfig(({ mode }): UserConfig => {
  const {
    VITE_APP_NAME,
    VITE_APP_FAVICON_SVG,
    API_SERVER_TARGET,
    PHOENIX_SERVER_TARGET,
  } = { ...DEFAULT_ENV, ...loadEnv(mode, process.cwd()) };

  return {
    plugins: [
      {
        name: 'constants',
        transformIndexHtml(html) {
          return html
            .replace(/%__APP_NAME__%/g, VITE_APP_NAME)
            .replace(/%__APP_FAVICON_SVG__%/g, VITE_APP_FAVICON_SVG);
        },
      },
      react(),
      svgr({
        include: '**/*.svg',
      }),
    ],
    define: {
      __APP_NAME__: JSON.stringify(VITE_APP_NAME),
      __PHOENIX_SERVER_TARGET__: JSON.stringify(PHOENIX_SERVER_TARGET),
    },
    server: {
      proxy: {
        '/api': {
          target: API_SERVER_TARGET,
        },
        '/phoenix': {
          target: PHOENIX_SERVER_TARGET,
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
