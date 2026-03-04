import fs from "node:fs";
import path from "node:path";

import type { Connect, Plugin } from "vite";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const OUTPUTS_DIR = path.resolve(__dirname, "../outputs");

const CONTENT_TYPES: Record<string, string> = {
  ".csv": "text/csv; charset=utf-8",
  ".geojson": "application/geo+json; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml; charset=utf-8"
};

function attachOutputsMiddleware(middlewares: Connect.Server) {
  middlewares.use("/outputs", (req, res, next) => {
    const requestPath = req.url?.split("?")[0] ?? "/";
    const relativePath = requestPath.replace(/^\/+/, "");
    const filePath = path.resolve(OUTPUTS_DIR, relativePath);
    if (!filePath.startsWith(OUTPUTS_DIR)) {
      res.statusCode = 403;
      res.end("Forbidden");
      return;
    }
    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
      next();
      return;
    }
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Content-Type", CONTENT_TYPES[path.extname(filePath).toLowerCase()] ?? "application/octet-stream");
    fs.createReadStream(filePath).pipe(res);
  });
}

function serveOutputsPlugin(): Plugin {
  return {
    name: "serve-econode25-outputs",
    configureServer(server) {
      attachOutputsMiddleware(server.middlewares);
    },
    configurePreviewServer(server) {
      attachOutputsMiddleware(server.middlewares);
    }
  };
}

export default defineConfig({
  plugins: [react(), serveOutputsPlugin()],
  server: {
    host: "0.0.0.0",
    port: 5173
  }
});
