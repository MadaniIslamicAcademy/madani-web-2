"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import type { User } from "@/lib/types";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(pathname === "/login");

  useEffect(() => {
    if (pathname === "/login") {
      setReady(true);
      return;
    }
    apiFetch<User>("/auth/me")
      .then(() => setReady(true))
      .catch(() => router.replace("/login"));
  }, [pathname, router]);

  if (!ready) return <div className="screen-loader"><div className="spinner" /><p>Loading secure workspace</p></div>;
  return <>{children}</>;
}
