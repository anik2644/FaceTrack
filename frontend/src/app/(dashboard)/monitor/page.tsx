"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Play, Square, Radio, Gauge, Users, VideoOff } from "lucide-react";
import toast from "react-hot-toast";
import { Badge, Button, Card, EmptyState, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { statusColor } from "@/lib/utils";
import type { Camera, DetectionEvent, StreamStatus } from "@/types";

export default function MonitorPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [sourceKind, setSourceKind] = useState("webcam");
  const [savedId, setSavedId] = useState<string>("");
  const [webcamIndex, setWebcamIndex] = useState("0");
  const [rtspUrl, setRtspUrl] = useState("");
  const [status, setStatus] = useState<StreamStatus | null>(null);
  const [events, setEvents] = useState<DetectionEvent[]>([]);
  const [busy, setBusy] = useState(false);
  const [feedNonce, setFeedNonce] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const active = status?.active ?? false;

  useEffect(() => {
    api.listCameras().then(setCameras).catch(() => undefined);
    api.streamStatus().then(setStatus).catch(() => undefined);
  }, []);

  // Poll status while active for live FPS/detection counts.
  useEffect(() => {
    if (!active) return;
    const id = setInterval(() => {
      api.streamStatus().then(setStatus).catch(() => undefined);
    }, 3000);
    return () => clearInterval(id);
  }, [active]);

  const connectWs = useCallback(() => {
    const ws = new WebSocket(api.wsUrl());
    ws.onmessage = (msg) => {
      try {
        const evt = JSON.parse(msg.data) as DetectionEvent;
        setEvents((prev) => [evt, ...prev].slice(0, 40));
      } catch {
        /* ignore malformed */
      }
    };
    ws.onclose = () => {
      wsRef.current = null;
    };
    wsRef.current = ws;
  }, []);

  const buildPayload = () => {
    if (sourceKind === "saved") {
      return { camera_id: Number(savedId) };
    }
    if (sourceKind === "webcam") {
      return { source_type: "webcam", source: webcamIndex, camera_name: "Webcam" };
    }
    return { source_type: "rtsp", source: rtspUrl, camera_name: "RTSP Camera" };
  };

  const start = async () => {
    if (sourceKind === "saved" && !savedId) {
      toast.error("Select a saved camera.");
      return;
    }
    if (sourceKind === "rtsp" && !rtspUrl) {
      toast.error("Enter an RTSP URL.");
      return;
    }
    setBusy(true);
    try {
      const s = await api.startStream(buildPayload());
      setStatus(s);
      setEvents([]);
      setFeedNonce(Date.now());
      connectWs();
      toast.success("Recognition started");
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const stop = async () => {
    setBusy(true);
    try {
      await api.stopStream();
      wsRef.current?.close();
      setStatus({ ...(status as StreamStatus), active: false });
      toast.success("Recognition stopped");
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => () => wsRef.current?.close(), []);

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div className="space-y-4 lg:col-span-2">
        <Card className="p-0 overflow-hidden">
          <div className="relative aspect-video bg-slate-900">
            {active ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={`${api.feedUrl()}?t=${feedNonce}`}
                alt="Live feed"
                className="h-full w-full object-contain"
              />
            ) : (
              <div className="flex h-full flex-col items-center justify-center gap-2 text-slate-500">
                <VideoOff className="h-10 w-10" />
                <p className="text-sm">Stream is offline. Configure a source and start.</p>
              </div>
            )}
            {active && (
              <div className="absolute left-3 top-3 flex items-center gap-2 rounded-full bg-red-600/90 px-3 py-1 text-xs font-semibold text-white">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-pulse-ring rounded-full bg-white" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-white" />
                </span>
                LIVE
              </div>
            )}
          </div>
        </Card>

        <div className="grid grid-cols-3 gap-3">
          <MiniStat icon={Gauge} label="FPS" value={status?.fps?.toFixed(1) ?? "0.0"} />
          <MiniStat icon={Radio} label="Detections" value={status?.detections ?? 0} />
          <MiniStat icon={Users} label="Gallery" value={status?.known_faces ?? 0} />
        </div>
      </div>

      <div className="space-y-4">
        <Card>
          <h2 className="mb-4 font-semibold text-slate-800">Source</h2>
          <div className="space-y-3">
            <Select
              label="Input type"
              value={sourceKind}
              onChange={(e) => setSourceKind(e.target.value)}
              disabled={active}
            >
              <option value="webcam">Local Webcam</option>
              <option value="rtsp">RTSP / IP Camera</option>
              <option value="saved">Saved Camera</option>
            </Select>

            {sourceKind === "webcam" && (
              <Input2
                label="Device index"
                value={webcamIndex}
                onChange={setWebcamIndex}
                disabled={active}
              />
            )}
            {sourceKind === "rtsp" && (
              <Input2
                label="RTSP URL"
                value={rtspUrl}
                onChange={setRtspUrl}
                placeholder="rtsp://user:pass@ip:554/stream"
                disabled={active}
              />
            )}
            {sourceKind === "saved" && (
              <Select
                label="Camera"
                value={savedId}
                onChange={(e) => setSavedId(e.target.value)}
                disabled={active}
              >
                <option value="">Select…</option>
                {cameras.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.source_type})
                  </option>
                ))}
              </Select>
            )}

            {active ? (
              <Button variant="danger" className="w-full" onClick={stop} loading={busy}>
                <Square className="h-4 w-4" /> Stop
              </Button>
            ) : (
              <Button className="w-full" onClick={start} loading={busy}>
                <Play className="h-4 w-4" /> Start Recognition
              </Button>
            )}
          </div>
        </Card>

        <Card>
          <h2 className="mb-3 font-semibold text-slate-800">Live Detections</h2>
          <div className="max-h-96 space-y-2 overflow-y-auto">
            {events.length === 0 ? (
              <EmptyState message="Recognised people will appear here." />
            ) : (
              events.map((e, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-lg border border-slate-100 p-2.5"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-700">{e.name}</p>
                    <p className="text-xs text-slate-400">
                      {e.timestamp} · {(e.confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                  <Badge className={statusColor(e.marked ? e.status : "default")}>
                    {e.marked ? e.status : "seen"}
                  </Badge>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

function MiniStat({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Gauge;
  label: string;
  value: string | number;
}) {
  return (
    <div className="card flex items-center gap-3 p-4">
      <Icon className="h-5 w-5 text-brand-600" />
      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className="text-lg font-bold text-slate-800">{value}</p>
      </div>
    </div>
  );
}

function Input2({
  label,
  value,
  onChange,
  ...rest
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  disabled?: boolean;
}) {
  return (
    <div>
      <label className="label">{label}</label>
      <input
        className="input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        {...rest}
      />
    </div>
  );
}
