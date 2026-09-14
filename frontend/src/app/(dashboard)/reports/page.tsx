"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Download, RefreshCw } from "lucide-react";
import toast from "react-hot-toast";
import { Button, Card, EmptyState, Input, Spinner } from "@/components/ui";
import { api, tokenStore } from "@/lib/api";
import { daysAgoISO, todayISO } from "@/lib/utils";
import type { DailyTrendPoint, ReportRow } from "@/types";

export default function ReportsPage() {
  const [start, setStart] = useState(daysAgoISO(30));
  const [end, setEnd] = useState(todayISO());
  const [rows, setRows] = useState<ReportRow[]>([]);
  const [trend, setTrend] = useState<DailyTrendPoint[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [summary, t] = await Promise.all([
        api.reportSummary({ start_date: start, end_date: end }),
        api.reportTrend({ start_date: start, end_date: end }),
      ]);
      setRows(summary);
      setTrend(t);
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [start, end]);

  useEffect(() => {
    load();
  }, [load]);

  const exportCsv = async () => {
    try {
      const url = api.exportCsvUrl({ start_date: start, end_date: end });
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${tokenStore.get()}` },
      });
      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `attendance_${start}_${end}.csv`;
      link.click();
      URL.revokeObjectURL(link.href);
    } catch (err) {
      toast.error((err as Error).message);
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div className="flex flex-wrap items-end gap-3">
            <div className="w-40">
              <Input label="From" type="date" value={start} onChange={(e) => setStart(e.target.value)} />
            </div>
            <div className="w-40">
              <Input label="To" type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
            </div>
            <Button variant="secondary" onClick={load}>
              <RefreshCw className="h-4 w-4" /> Refresh
            </Button>
          </div>
          <Button onClick={exportCsv}>
            <Download className="h-4 w-4" /> Export CSV
          </Button>
        </div>
      </Card>

      <Card>
        <h2 className="mb-4 font-semibold text-slate-800">Daily Attendance Trend</h2>
        {trend.length === 0 ? (
          <EmptyState message="No data for the selected range." />
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="event_date" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="present" stackId="a" fill="#22c55e" radius={[0, 0, 0, 0]} />
              <Bar dataKey="late" stackId="a" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </Card>

      <Card className="p-0">
        <h2 className="p-5 pb-0 font-semibold text-slate-800">Per-Person Summary</h2>
        {loading ? (
          <Spinner />
        ) : rows.length === 0 ? (
          <EmptyState message="No summary data available." />
        ) : (
          <div className="overflow-x-auto p-5">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-slate-500">
                  <th className="py-2">Name</th>
                  <th>Employee ID</th>
                  <th>Department</th>
                  <th>Days Present</th>
                  <th>Days Late</th>
                  <th>Avg Confidence</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.person_id} className="border-b last:border-0">
                    <td className="py-2.5 font-medium text-slate-700">{r.name}</td>
                    <td className="text-slate-500">{r.employee_id || "—"}</td>
                    <td className="text-slate-500">{r.department || "—"}</td>
                    <td className="text-green-600">{r.days_present}</td>
                    <td className="text-amber-600">{r.days_late}</td>
                    <td className="text-slate-500">
                      {(r.avg_confidence * 100).toFixed(0)}%
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
