import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// O proxy faz o navegador enxergar front e API no mesmo endereço:
// tudo que começa com /api é repassado para o back-end em Python.
const proxy = { "/api": "http://localhost:8000" };

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy },
  preview: { port: 5173, proxy },
});
