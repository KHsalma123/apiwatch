import axios from "axios";

const TOKEN_KEY = "apiwatch_token";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL || "") + "/api/v1",
  timeout: 45000, // a manual check can take up to 30 s
});

api.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    const url = error.config?.url || "";
    if (error.response?.status === 401 && !url.startsWith("/auth/")) {
      tokenStore.clear();
      window.dispatchEvent(new Event("auth:logout")); // AuthContext reacts to this
    }
    return Promise.reject(error);
  }
);

/** Turns any API error into a readable sentence. */
export function errorMessage(error) {
  if (!error.response) return "Cannot reach the server. Check your connection and try again.";
  const { status, data } = error.response;
  if (status === 429) return "Too many requests. Wait a minute and try again.";
  const detail = data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) {
    const first = detail[0];
    const field = first.loc?.slice(1).join(".");
    const msg = (first.msg || "Invalid value").replace(/^Value error, /, "");
    return field ? `${field}: ${msg}` : msg;
  }
  return `Something went wrong (error ${status}).`;
}

export default api;
