"use client";

import { useEffect, useState } from "react";
import {
  Users,
  UserCheck,
  Clock,
  UserX,
  Activity,
  Database,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import toast from "react-hot-toast";
import StatCard from "@/components/StatCard";
import { Card, Spinner, EmptyState, Badge } from "@/components/ui";
import { api } from "@/lib/api";
import { daysAgoISO, todayISO, statusColor, formatPercent } from "@/lib/utils";
import type {
  AttendanceRecord,
  AttendanceStats,
  DailyTrendPoint,
  ModelStatus,
} from "@/types";

export default function DashboardPage() {
  const [stats, setStats] = useState<AttendanceStats | null>(null);
  const [trend, setTrend] = useState<DailyTrendPoint[]>([]);
  const [today, setToday] = useState<AttendanceRecord[]>([]);
  const [model, setModel] = useState<ModelStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [s, t, td, m] = await Promise.all([
          api.attendanceStats(),
          api.reportTrend({ start_date: daysAgoISO(6), end_date: todayISO() }),
          api.attendanceToday(),
          api.modelStatus(),
        ]);
        setStats(s);
        setTrend(t);
        setToday(td);
        setModel(m);
      } catch (err) {
        toast.error((err as Error).message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <Spinner />;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Registered" value={stats?.total_persons ?? 0} icon={Users} />
        <StatCard
          label="Present Today"
          value={stats?.present_today ?? 0}
          icon={UserCheck}
          accent="green"
        />
        <StatCard
          label="Late Today"
          value={stats?.late_today ?? 0}
          icon={Clock}
          accent="amber"
        />
        <StatCard
          label="Absent"
          value={stats?.absent_today ?? 0}
          icon={UserX}
          accent="red"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-semibold text-slate-800">Attendance — Last 7 Days</h2>
            <Badge className="bg-brand-50 text-brand-600">
              Rate: {formatPercent(stats?.attendance_rate ?? 0)}
            </Badge>
          </div>
          {trend.length === 0 ? (
            <EmptyState message="No attendance data yet." />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={trend}>
                <defs>
                  <linearGradient id="present" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="late" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="event_date" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="present"
                  stroke="#22c55e"
                  fill="url(#present)"
                  strokeWidth={2}
                />
                <Area
                  type="monotone"
                  dataKey="late"
                  stroke="#f59e0b"
                  fill="url(#late)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card>
          <h2 className="mb-4 font-semibold text-slate-800">System Status</h2>
          <div className="space-y-4">
            <StatusRow
              icon={Activity}
              label="Person Detector (YOLO)"
              ok={!!model?.yolo_loaded}
            />
            <StatusRow
              icon={Activity}
              label="Face Engine (dlib)"
              ok={!!model?.face_recognition_available}
            />
            <div className="flex items-center gap-3 rounded-lg bg-slate-50 p-3">
              <Database className="h-5 w-5 text-brand-600" />
              <div>
                <p className="text-sm font-medium text-slate-700">Gallery Size</p>
                <p className="text-xs text-slate-500">
                  {model?.known_faces ?? 0} encodings loaded
                </p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <h2 className="mb-4 font-semibold text-slate-800">Today&apos;s Check-ins</h2>
        {today.length === 0 ? (
          <EmptyState message="No check-ins recorded today." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-slate-500">
                  <th className="py-2">Name</th>
                  <th>Department</th>
                  <th>Time</th>
                  <th>Confidence</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {today.map((r) => (
                  <tr key={r.id} className="border-b last:border-0">
                    <td className="py-2.5 font-medium text-slate-700">{r.name}</td>
                    <td className="text-slate-500">{r.department || "—"}</td>
                    <td className="text-slate-500">
                      {new Date(r.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="text-slate-500">
                      {(r.confidence * 100).toFixed(0)}%
                    </td>
                    <td>
                      <Badge className={statusColor(r.status)}>{r.status}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

function StatusRow({
  icon: Icon,
  label,
  ok,
}: {
  icon: typeof Activity;
  label: string;
  ok: boolean;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg bg-slate-50 p-3">
      <div className="flex items-center gap-3">
        <Icon className="h-5 w-5 text-slate-400" />
        <span className="text-sm font-medium text-slate-700">{label}</span>
      </div>
      <Badge className={ok ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}>
        {ok ? "Online" : "Unavailable"}
      </Badge>
    </div>
  );
}
