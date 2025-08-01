// config.js
// Central config for API gateway or microservice URLs
// Uses environment variable if available, falls back to default
export const API_GATEWAY_URL = import.meta.env?.VITE_API_GATEWAY_URL || "http://localhost:8000"; // Change as needed for deployment
