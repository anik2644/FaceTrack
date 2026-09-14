"use client";

import { useEffect, useState } from "react";
import { Cctv, Plus, Trash2, Wifi } from "lucide-react";
import toast from "react-hot-toast";
import { Badge, Button, Card, EmptyState, Input, Modal, Select, Spinner } from "@/components/ui";
import { api } from "@/lib/api";
import type { Camera } from "@/types";

const EMPTY = { name: "", source_type: "webcam", source: "0", location: "" };

export default function CamerasPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      setCameras(await api.listCameras());
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await api.createCamera(form);
      toast.success("Camera added");
      setOpen(false);
      setForm(EMPTY);
      load();
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const test = async () => {
    setTesting(true);
    try {
      const res = await api.testCamera({
        source_type: form.source_type,
        source: form.source,
      });
      res.success ? toast.success(res.message) : toast.error(res.message);
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setTesting(false);
    }
  };

  const remove = async (c: Camera) => {
    if (!confirm(`Delete camera "${c.name}"?`)) return;
    try {
      await api.deleteCamera(c.id);
      toast.success("Camera deleted");
      load();
    } catch (err) {
      toast.error((err as Error).message);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setOpen(true)}>
          <Plus className="h-4 w-4" /> Add Camera
        </Button>
      </div>

      {loading ? (
        <Spinner />
      ) : cameras.length === 0 ? (
        <Card>
          <EmptyState message="No cameras configured yet." />
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cameras.map((c) => (
            <Card key={c.id}>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-brand-50 p-2.5 text-brand-600">
                    <Cctv className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-semibold text-slate-800">{c.name}</p>
                    <p className="text-xs text-slate-400">{c.location || "No location"}</p>
                  </div>
                </div>
                <button
                  onClick={() => remove(c)}
                  className="rounded-lg p-2 text-red-500 hover:bg-red-50"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              <div className="mt-4 flex items-center justify-between">
                <Badge className="bg-slate-100 text-slate-600 uppercase">
                  {c.source_type}
                </Badge>
                <Badge
                  className={
                    c.is_active
                      ? "bg-green-100 text-green-700"
                      : "bg-slate-100 text-slate-500"
                  }
                >
                  {c.is_active ? "Active" : "Inactive"}
                </Badge>
              </div>
              <p className="mt-2 truncate text-xs text-slate-400" title={c.source}>
                {c.source}
              </p>
            </Card>
          ))}
        </div>
      )}

      <Modal open={open} onClose={() => setOpen(false)} title="Add Camera">
        <div className="space-y-3">
          <Input
            label="Name *"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <Select
            label="Source type"
            value={form.source_type}
            onChange={(e) => setForm({ ...form, source_type: e.target.value })}
          >
            <option value="webcam">Webcam</option>
            <option value="rtsp">RTSP</option>
            <option value="http">HTTP</option>
          </Select>
          <Input
            label="Source (device index or URL) *"
            value={form.source}
            onChange={(e) => setForm({ ...form, source: e.target.value })}
          />
          <Input
            label="Location"
            value={form.location}
            onChange={(e) => setForm({ ...form, location: e.target.value })}
          />
          <div className="flex justify-between gap-2 pt-2">
            <Button variant="secondary" onClick={test} loading={testing}>
              <Wifi className="h-4 w-4" /> Test
            </Button>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button onClick={save} loading={saving} disabled={!form.name || !form.source}>
                Save
              </Button>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
}
