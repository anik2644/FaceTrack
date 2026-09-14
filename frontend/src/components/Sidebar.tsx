"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  UserPlus,
  Video,
  CalendarCheck,
  BarChart3,
  Cctv,
  Settings,
  ScanFace,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/monitor", label: "Live Monitor", icon: Video },
  { href: "/persons", label: "Persons", icon: Users },
  { href: "/register", label: "Enroll", icon: UserPlus },
  { href: "/attendance", label: "Attendance", icon: CalendarCheck },
  { href: "/reports", label: "Reports", icon: BarChart3 },
  { href: "/cameras", label: "Cameras", icon: Cctv },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-slate-900 text-slate-300">
      <div className="flex items-center gap-2 px-6 py-5 text-white">
        <ScanFace className="h-7 w-7 text-brand-400" />
        <span className="text-xl font-bold tracking-tight">FaceTrack</span>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-2">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition",
                active
                  ? "bg-brand-600 text-white"
                  : "hover:bg-slate-800 hover:text-white"
              )}
            >
              <Icon className="h-5 w-5" />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="px-6 py-4 text-xs text-slate-500">
        v1.0.0 · Real-time CV
      </div>
    </aside>
  );
}
