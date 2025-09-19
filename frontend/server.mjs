#!/usr/bin/env node
import { createServer } from "node:http";
import { createReadStream } from "node:fs";
import { stat, readFile } from "node:fs/promises";
import { extname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const PUBLIC_DIR = resolve(__dirname, "public");
const SRC_DIR = resolve(__dirname, "src");

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".svg": "image/svg+xml",
};

function resolveFile(pathname) {
  if (pathname === "/") {
    return join(PUBLIC_DIR, "index.html");
  }
  if (pathname.startsWith("/src/")) {
    return join(SRC_DIR, pathname.replace("/src/", ""));
  }
  return join(PUBLIC_DIR, pathname);
}

const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const filePath = resolveFile(url.pathname);
    const fileStat = await stat(filePath);
    if (fileStat.isDirectory()) {
      res.writeHead(403);
      res.end("Directory access is not permitted");
      return;
    }
    const mime = MIME_TYPES[extname(filePath).toLowerCase()] ?? "application/octet-stream";
    res.writeHead(200, { "Content-Type": mime });
    createReadStream(filePath).pipe(res);
  } catch (error) {
    if (error.code === "ENOENT") {
      try {
        const fallback = await readFile(join(PUBLIC_DIR, "index.html"));
        res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
        res.end(fallback);
      } catch (fallbackError) {
        res.writeHead(404);
        res.end("Not found");
      }
      return;
    }
    res.writeHead(500);
    res.end("Internal server error");
  }
});

const port = Number.parseInt(process.env.PORT ?? "4173", 10);
server.listen(port, () => {
  console.log(`Static server running on http://localhost:${port}`);
});