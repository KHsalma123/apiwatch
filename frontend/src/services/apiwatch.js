import api from "./api";

const data = (p) => p.then((r) => r.data);

export const authApi = {
  register: (body) => data(api.post("/auth/register", body)),
  login: (body) => data(api.post("/auth/login", body)),
  me: () => data(api.get("/users/me")),
  updateMe: (body) => data(api.patch("/users/me", body)),
  changePassword: (body) => api.post("/users/me/change-password", body),
};

export const monitorsApi = {
  list: (params) => data(api.get("/monitors", { params })),
  get: (id) => data(api.get(`/monitors/${id}`)),
  create: (body) => data(api.post("/monitors", body)),
  update: (id, body) => data(api.put(`/monitors/${id}`, body)),
  setActive: (id, is_active) => data(api.patch(`/monitors/${id}/active`, { is_active })),
  remove: (id) => api.delete(`/monitors/${id}`),
  check: (id) => data(api.post(`/monitors/${id}/check`)),
  results: (id, params) => data(api.get(`/monitors/${id}/results`, { params })),
  stats: (id, range) => data(api.get(`/monitors/${id}/stats`, { params: { range } })),
  chart: (id, range) => data(api.get(`/monitors/${id}/chart`, { params: { range } })),
  incidents: (id, params) => data(api.get(`/monitors/${id}/incidents`, { params })),
};

export const incidentsApi = {
  list: (params) => data(api.get("/incidents", { params })),
};

export const dashboardApi = {
  summary: () => data(api.get("/dashboard/summary")),
  charts: (range) => data(api.get("/dashboard/charts", { params: { range } })),
};
