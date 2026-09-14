// Shared domain types mirroring the backend Pydantic schemas.

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface Person {
  id: number;
  name: string;
  employee_id: string | null;
  department: string | null;
  email: string | null;
  phone: string | null;
  is_active: boolean;
  photo_path: string | null;
  encoding_count: number;
  created_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface AttendanceRecord {
  id: number;
  person_id: number;
  name: string;
  employee_id: string | null;
  department: string | null;
  event_date: string;
  timestamp: string;
  confidence: number;
  status: string;
  camera_name: string | null;
  snapshot_path: string | null;
}

export interface AttendanceStats {
  total_persons: number;
  present_today: number;
  late_today: number;
  absent_today: number;
  attendance_rate: number;
  total_records: number;
}

export interface ReportRow {
  person_id: number;
  name: string;
  employee_id: string | null;
  department: string | null;
  days_present: number;
  days_late: number;
  avg_confidence: number;
}

export interface DailyTrendPoint {
  event_date: string;
  present: number;
  late: number;
}

export interface Camera {
  id: number;
  name: string;
  source_type: "webcam" | "rtsp" | "http";
  source: string;
  location: string | null;
  is_active: boolean;
  created_at: string;
}

export interface StreamStatus {
  active: boolean;
  camera_name: string | null;
  source: string | null;
  fps: number;
  detections: number;
  known_faces: number;
}

export interface ModelStatus {
  yolo_loaded: boolean;
  face_recognition_available: boolean;
  known_faces: number;
  yolo_model_path: string;
}

export interface DetectionEvent {
  name: string;
  person_id: number | null;
  confidence: number;
  status: string;
  timestamp: string;
  marked: boolean;
}
