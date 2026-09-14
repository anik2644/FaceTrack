import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

export function daysAgoISO(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function statusColor(status: string): string {
  switch (status) {
    case "present":
      return "bg-green-100 text-green-700";
    case "late":
      return "bg-amber-100 text-amber-700";
    case "absent":
      return "bg-red-100 text-red-700";
    default:
      return "bg-slate-100 text-slate-600";
  }
}
