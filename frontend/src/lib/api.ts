"use client";

import axios, { AxiosInstance } from "axios";
import type {
  AttendanceRecord,
  AttendanceStats,
  Camera,
  DailyTrendPoint,
  ModelStatus,
  Page,
  Person,
  ReportRow,
  StreamStatus,
  Token,
  User,
} from "@/types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const API_PREFIX = process.env.NEXT_PUBLIC_API_PREFIX ?? "/api/v1";
export const API_URL = `${API_BASE}${API_PREFIX}`;

const TOKEN_KEY = "facetrack_token";

export const tokenStore = {
  get: () => (typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null),
  set: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

const client: AxiosInstance = axios.create({ baseURL: API_URL });

client.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      tokenStore.clear();
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    const message =
      error.response?.data?.error ||
      error.response?.data?.detail ||
      error.message ||
      "Request failed";
    return Promise.reject(new Error(typeof message === "string" ? message : "Request failed"));
  }
);

// ----- API surface (one typed function per endpoint) -----------------------
export const api = {
  // Auth
  login: (username: string, password: string) =>
    client.post<Token>("/auth/login", { username, password }).then((r) => r.data),
  me: () => client.get<User>("/auth/me").then((r) => r.data),

  // System
  health: () => client.get("/health").then((r) => r.data),
  modelStatus: () => client.get<ModelStatus>("/model-status").then((r) => r.data),

  // Persons
  listPersons: (params?: Record<string, unknown>) =>
    client.get<Page<Person>>("/persons", { params }).then((r) => r.data),
  getPerson: (id: number) => client.get<Person>(`/persons/${id}`).then((r) => r.data),
  createPerson: (payload: Record<string, unknown>) =>
    client.post<Person>("/persons", payload).then((r) => r.data),
  updatePerson: (id: number, payload: Record<string, unknown>) =>
    client.patch<Person>(`/persons/${id}`, payload).then((r) => r.data),
  addEncoding: (id: number, image: string) =>
    client.post<Person>(`/persons/${id}/encodings`, { image }).then((r) => r.data),
  deletePerson: (id: number) => client.delete(`/persons/${id}`).then((r) => r.data),
  departments: () => client.get<string[]>("/persons/departments").then((r) => r.data),

  // Attendance
  attendanceToday: () =>
    client.get<AttendanceRecord[]>("/attendance/today").then((r) => r.data),
  attendanceStats: () =>
    client.get<AttendanceStats>("/attendance/stats").then((r) => r.data),
  attendanceRange: (params: Record<string, unknown>) =>
    client.get<AttendanceRecord[]>("/attendance", { params }).then((r) => r.data),

  // Reports
  reportSummary: (params: Record<string, unknown>) =>
    client.get<ReportRow[]>("/reports/summary", { params }).then((r) => r.data),
  reportTrend: (params: Record<string, unknown>) =>
    client.get<DailyTrendPoint[]>("/reports/trend", { params }).then((r) => r.data),
  exportCsvUrl: (params: Record<string, string>) =>
    `${API_URL}/reports/export?${new URLSearchParams(params).toString()}`,

  // Cameras
  listCameras: () => client.get<Camera[]>("/cameras").then((r) => r.data),
  createCamera: (payload: Record<string, unknown>) =>
    client.post<Camera>("/cameras", payload).then((r) => r.data),
  updateCamera: (id: number, payload: Record<string, unknown>) =>
    client.patch<Camera>(`/cameras/${id}`, payload).then((r) => r.data),
  deleteCamera: (id: number) => client.delete(`/cameras/${id}`).then((r) => r.data),
  testCamera: (payload: Record<string, unknown>) =>
    client.post("/cameras/test", payload).then((r) => r.data),

  // Recognition
  startStream: (payload: Record<string, unknown>) =>
    client.post<StreamStatus>("/recognition/start", payload).then((r) => r.data),
  stopStream: () => client.post("/recognition/stop").then((r) => r.data),
  streamStatus: () =>
    client.get<StreamStatus>("/recognition/status").then((r) => r.data),
  snapshot: (payload: Record<string, unknown>) =>
    client.post<{ success: boolean; image: string }>("/recognition/snapshot", payload).then((r) => r.data),

  feedUrl: () => `${API_URL}/recognition/feed`,
  wsUrl: () =>
    `${API_BASE.replace(/^http/, "ws")}${API_PREFIX}/recognition/ws`,
};

export default client;
