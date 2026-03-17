import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0', // 允许局域网访问
    allowedHosts: true, // 核心修复：允许 cpolar 等所有外部主机访问
  },
});