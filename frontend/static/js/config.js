/**
 * DocIntel AI Platform — Frontend Configuration
 *
 * Set API_BASE_URL to your deployed backend URL (Render/Railway etc.) when deploying.
 * For local development, it defaults to localhost:8000.
 *
 * ⚠️ Do NOT commit real API URLs if they contain secrets.
 *    For production, this file is the only place to update the backend URL.
 */

const CONFIG = {
  // ─── Change this to your deployed Render backend URL ──────────────────────
  // Example: "https://docintel-api.onrender.com"
  API_BASE_URL: window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://localhost:8000"
    : "https://YOUR_RENDER_BACKEND_URL.onrender.com",  // <-- Replace before deploying
};
