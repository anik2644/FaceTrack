"use client";

import { useCallback, useEffect, useState } from "react";
import { Filter } from "lucide-react";
import toast from "react-hot-toast";
import { Badge, Button, Card, EmptyState, Input, Select, Spinner } from "@/components/ui";
import { api } from "@/lib/api";
import { daysAgoISO, statusColor, todayISO } from "@/lib/utils";
import type { AttendanceRecord } from "@/types";

export default function AttendancePage() {
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [departments, setDepartments] = useState<string[]>([]);
  const [start, setStart] = useState(daysAgoISO(7));
  const [end, setEnd] = useState(todayISO());
  const [department, setDepartment] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.attendanceRange({
        start_date: start,
        end_date: end,
        department: department || undefined,
      });
      setRecords(data);
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [start, end, department]);

  useEffect(() => {
    api.departments().then(setDepartments).catch(() => undefined);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex flex-wrap items-end gap-3">
          <div className="w-40">
            <Input label="From" type="date" value={start} onChange={(e) => setStart(e.target.value)} />
          </div>
          <div className="w-40">
            <Input label="To" type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
          </div>
          <div className="w-48">
            <Select
              label="Department"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
            >
              <option value="">All departments</option>
              {departments.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </Select>
          </div>
          <Button onClick={load}>
            <Filter className="h-4 w-4" /> Apply
          </Button>
        </div>
      </Card>

      <Card className="p-0">
        {loading ? (
          <Spinner />
        ) : records.length === 0 ? (
          <EmptyState message="No attendance records for this range." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-slate-50 text-left text-slate-500">
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4">Time</th>
                  <th className="px-4">Name</th>
                  <th className="px-4">Department</th>
                  <th className="px-4">Camera</th>
                  <th className="px-4">Confidence</th>
                  <th className="px-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id} className="border-b last:border-0 hover:bg-slate-50">
                    <td className="px-4 py-2.5 text-slate-600">{r.event_date}</td>
                    <td className="px-4 text-slate-500">
                      {new Date(r.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-4 font-medium text-slate-700">{r.name}</td>
                    <td className="px-4 text-slate-500">{r.department || "—"}</td>
                    <td className="px-4 text-slate-500">{r.camera_name || "—"}</td>
                    <td className="px-4 text-slate-500">
                      {(r.confidence * 100).toFixed(0)}%
                    </td>
                    <td className="px-4">
                      <Badge className={statusColor(r.status)}>{r.status}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      <p className="text-xs text-slate-400">{records.length} record(s)</p>
    </div>
  );
}
