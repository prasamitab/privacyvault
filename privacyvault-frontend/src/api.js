import axios from "axios";

export const BACKEND_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const api = axios.create({
  baseURL: BACKEND_URL,
  timeout: 120000,
});

export default api;
