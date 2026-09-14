"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { UserPlus } from "lucide-react";
import toast from "react-hot-toast";
import { Button, Card, Input } from "@/components/ui";
import WebcamCapture from "@/components/WebcamCapture";
import { api } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    name: "",
    employee_id: "",
    department: "",
    email: "",
    phone: "",
  });
  const [captured, setCaptured] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const update = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!captured) {
      toast.error("Please capture or upload a face photo.");
      return;
    }
    setSaving(true);
    try {
      await api.createPerson({ ...form, image: captured });
      toast.success(`${form.name} enrolled successfully`);
      router.push("/persons");
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={submit} className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <Card>
        <h2 className="mb-4 font-semibold text-slate-800">Face Enrollment</h2>
        <WebcamCapture captured={captured} onCapture={(d) => setCaptured(d || null)} />
        <p className="mt-3 text-xs text-slate-400">
          Ensure the face is centred, well-lit and unobstructed for best results.
        </p>
      </Card>

      <Card>
        <h2 className="mb-4 font-semibold text-slate-800">Details</h2>
        <div className="space-y-4">
          <Input label="Full Name *" value={form.name} onChange={update("name")} required />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Employee ID" value={form.employee_id} onChange={update("employee_id")} />
            <Input label="Department" value={form.department} onChange={update("department")} />
          </div>
          <Input label="Email" type="email" value={form.email} onChange={update("email")} />
          <Input label="Phone" value={form.phone} onChange={update("phone")} />
          <Button type="submit" loading={saving} className="w-full">
            <UserPlus className="h-4 w-4" /> Enroll Person
          </Button>
        </div>
      </Card>
    </form>
  );
}
