import react from '@vitejs/plugin-react-swc';
import { resolve } from 'path';
import { fileURLToPath, URL } from 'url';
import { defineConfig } from 'vite';
import svgr from 'vite-plugin-svgr';

const phoenixServerTarget = 'http://localhost:6006';

export default defineConfig({
  plugins: [
    react(),
    svgr({
      include: '**/*.svg',
    }),
  ],
  define: {
    __APP_NAME__: JSON.stringify('BeeAI'),
    __PHOENIX_SERVER_TARGET__: JSON.stringify(phoenixServerTarget),
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8333',
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
});
