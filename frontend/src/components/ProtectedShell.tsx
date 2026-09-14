"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import Sidebar from "@/components/Sidebar";
import Topbar from "@/components/Topbar";
import { Spinner } from "@/components/ui";

const TITLES: Record<string, string> = {
  "/": "Dashboard",
  "/monitor": "Live Monitor",
  "/persons": "Registered Persons",
  "/register": "Enroll New Person",
  "/attendance": "Attendance",
  "/reports": "Reports & Analytics",
  "/cameras": "Camera Management",
  "/settings": "Settings",
};

export default function ProtectedShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner />
      </div>
    );
  }

  const title =
    TITLES[pathname] ??
    Object.entries(TITLES).find(([k]) => k !== "/" && pathname.startsWith(k))?.[1] ??
    "FaceTrack";

  return (
    <div className="min-h-screen">
      <Sidebar />
      <div className="ml-64 flex min-h-screen flex-col">
        <Topbar title={title} />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
