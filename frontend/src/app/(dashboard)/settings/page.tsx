"use client";

import { useEffect, useState } from "react";
import { Cpu, ScanFace, ShieldCheck, Database } from "lucide-react";
import { Badge, Card, Spinner } from "@/components/ui";
import { useAuth } from "@/lib/auth-context";
import { api, API_URL } from "@/lib/api";
import type { ModelStatus } from "@/types";

export default function SettingsPage() {
  const { user } = useAuth();
  const [model, setModel] = useState<ModelStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .modelStatus()
      .then(setModel)
      .catch(() => undefined)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <Card>
        <div className="mb-4 flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-brand-600" />
          <h2 className="font-semibold text-slate-800">Account</h2>
        </div>
        <dl className="space-y-3 text-sm">
          <Row label="Username" value={user?.username ?? "—"} />
          <Row label="Full name" value={user?.full_name ?? "—"} />
          <Row label="Email" value={user?.email ?? "—"} />
          <Row label="Role" value={user?.role ?? "—"} />
        </dl>
      </Card>

      <Card>
        <div className="mb-4 flex items-center gap-2">
          <Cpu className="h-5 w-5 text-brand-600" />
          <h2 className="font-semibold text-slate-800">Recognition Engine</h2>
        </div>
        <div className="space-y-3">
          <EngineRow
            icon={Cpu}
            label="Person Detector (YOLOv8)"
            ok={!!model?.yolo_loaded}
          />
          <EngineRow
            icon={ScanFace}
            label="Face Recognition (dlib)"
            ok={!!model?.face_recognition_available}
          />
          <div className="flex items-center justify-between rounded-lg bg-slate-50 p-3 text-sm">
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-slate-400" />
              <span className="text-slate-600">Gallery encodings</span>
            </div>
            <span className="font-semibold text-slate-800">{model?.known_faces ?? 0}</span>
          </div>
        </div>
      </Card>

      <Card className="lg:col-span-2">
        <h2 className="mb-4 font-semibold text-slate-800">API</h2>
        <dl className="space-y-3 text-sm">
          <Row label="Base URL" value={API_URL} />
          <Row label="Interactive docs" value={`${API_URL.replace(/\/api\/v1$/, "")}/docs`} />
          <Row label="Model weights" value={model?.yolo_model_path ?? "—"} />
        </dl>
      </Card>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-slate-500">{label}</dt>
      <dd className="max-w-[60%] truncate font-medium text-slate-700" title={value}>
        {value}
      </dd>
    </div>
  );
}

function EngineRow({
  icon: Icon,
  label,
  ok,
}: {
  icon: typeof Cpu;
  label: string;
  ok: boolean;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg bg-slate-50 p-3 text-sm">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-slate-400" />
        <span className="text-slate-600">{label}</span>
      </div>
      <Badge className={ok ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}>
        {ok ? "Loaded" : "Unavailable"}
      </Badge>
    </div>
  );
}
