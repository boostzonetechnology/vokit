import path from "node:path";
import { fileURLToPath } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const webUiSrc = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../packages/web-ui/src",
);

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": webUiSrc,
    },
  },
  server: {
    port: 5174,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
