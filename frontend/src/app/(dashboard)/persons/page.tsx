"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Search, Trash2, UserPlus, Camera as CameraIcon, ImagePlus } from "lucide-react";
import toast from "react-hot-toast";
import { Badge, Button, Card, EmptyState, Input, Modal, Spinner } from "@/components/ui";
import WebcamCapture from "@/components/WebcamCapture";
import { api } from "@/lib/api";
import type { Person } from "@/types";

export default function PersonsPage() {
  const [persons, setPersons] = useState<Person[]>([]);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [encodeFor, setEncodeFor] = useState<Person | null>(null);
  const [captured, setCaptured] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.listPersons({ query: query || undefined, size: 100 });
      setPersons(res.items);
      setTotal(res.total);
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [query]);

  useEffect(() => {
    const t = setTimeout(load, 300);
    return () => clearTimeout(t);
  }, [load]);

  const remove = async (person: Person) => {
    if (!confirm(`Delete ${person.name}? This removes all their data.`)) return;
    try {
      await api.deletePerson(person.id);
      toast.success("Person deleted");
      load();
    } catch (err) {
      toast.error((err as Error).message);
    }
  };

  const submitEncoding = async () => {
    if (!encodeFor || !captured) return;
    setSaving(true);
    try {
      await api.addEncoding(encodeFor.id, captured);
      toast.success("Face sample added");
      setEncodeFor(null);
      setCaptured(null);
      load();
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="relative w-full max-w-sm">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            className="input pl-9"
            placeholder="Search by name, ID or email..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <Link href="/register" className="btn-primary">
          <UserPlus className="h-4 w-4" /> Enroll Person
        </Link>
      </div>

      <Card className="p-0">
        {loading ? (
          <Spinner />
        ) : persons.length === 0 ? (
          <EmptyState message="No persons found. Enroll someone to get started." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-slate-50 text-left text-slate-500">
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4">Employee ID</th>
                  <th className="px-4">Department</th>
                  <th className="px-4">Samples</th>
                  <th className="px-4">Status</th>
                  <th className="px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {persons.map((p) => (
                  <tr key={p.id} className="border-b last:border-0 hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-slate-700">{p.name}</td>
                    <td className="px-4 text-slate-500">{p.employee_id || "—"}</td>
                    <td className="px-4 text-slate-500">{p.department || "—"}</td>
                    <td className="px-4">
                      <Badge className="bg-brand-50 text-brand-600">
                        {p.encoding_count} sample{p.encoding_count === 1 ? "" : "s"}
                      </Badge>
                    </td>
                    <td className="px-4">
                      <Badge
                        className={
                          p.is_active
                            ? "bg-green-100 text-green-700"
                            : "bg-slate-100 text-slate-500"
                        }
                      >
                        {p.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => {
                            setEncodeFor(p);
                            setCaptured(null);
                          }}
                          className="rounded-lg p-2 text-brand-600 hover:bg-brand-50"
                          title="Add face sample"
                        >
                          <ImagePlus className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => remove(p)}
                          className="rounded-lg p-2 text-red-500 hover:bg-red-50"
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      <p className="text-xs text-slate-400">{total} person(s) registered</p>

      <Modal
        open={!!encodeFor}
        onClose={() => setEncodeFor(null)}
        title={`Add face sample — ${encodeFor?.name ?? ""}`}
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-500">
            Capture an additional angle to improve recognition accuracy.
          </p>
          <WebcamCapture captured={captured} onCapture={(d) => setCaptured(d || null)} />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setEncodeFor(null)}>
              Cancel
            </Button>
            <Button onClick={submitEncoding} loading={saving} disabled={!captured}>
              <CameraIcon className="h-4 w-4" /> Save Sample
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
