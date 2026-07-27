"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { apiFetch, clearCsrfToken } from "@/lib/api";

const links = [
  ["/", "Dashboard", "⌂"],
  ["/campaigns", "Campaigns", "✦"],
  ["/calendar", "Calendar", "◫"],
  ["/connections", "Connections", "◎"],
  ["/leads", "Admission Leads", "✉"],
  ["/reports", "Reports", "▤"],
  ["/settings", "Settings", "⚙"],
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  if (pathname === "/login") return <>{children}</>;

  async function logout() {
    try { await apiFetch<void>("/auth/logout", { method: "POST" }); } catch {}
    clearCsrfToken();
    router.replace("/login");
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark">M</div><div><strong>Madani Social</strong><small>Automation Platform</small></div></div>
        <nav>
          {links.map(([href, label, icon]) => (
            <Link key={href} href={href} className={pathname === href || (href !== "/" && pathname.startsWith(href)) ? "active" : ""}>
              <span>{icon}</span>{label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="safe-dot" /> Approval mode enabled
          <button onClick={logout}>Sign out</button>
        </div>
      </aside>
      <main className="main-content">{children}</main>
    </div>
  );
}
