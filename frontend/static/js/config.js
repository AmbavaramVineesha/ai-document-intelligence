/**
 * DocIntel AI Platform — Frontend Configuration
 *
 * Set API_BASE_URL to your deployed backend URL (Render/Railway etc.) when deploying.
 * For local development, it defaults to localhost:8000.
 */

const CONFIG = {
  // ─── Backend URL ──────────────────────────────────────────────────────────
  API_BASE_URL: window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://localhost:8000"
    : "https://docintel-api-i9ep.onrender.com",
};
