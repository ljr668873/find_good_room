import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// 端口/地址与 start.sh 共用同一环境变量；单独跑 vite 时用默认值
const API_PORT = process.env.API_PORT || 8000;
const HOST = process.env.HOST || "0.0.0.0";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: HOST,
    port: Number(process.env.WEB_PORT) || 5173,
    strictPort: true, // 端口被占直接报错，避免悄悄换端口导致代理/提示对不上
    proxy: {
      "/api": `http://127.0.0.1:${API_PORT}`,
      "/uploads": `http://127.0.0.1:${API_PORT}`,
    },
  },
});
