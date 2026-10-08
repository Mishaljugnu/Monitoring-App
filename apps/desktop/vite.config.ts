import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ["react", "react-dom", "zustand"],
          charts: ["recharts"],
          icons: ["lucide-react"]
        }
      }
    }
  },
  server: {
    host: "127.0.0.1",
    port: 5173
  }
});
