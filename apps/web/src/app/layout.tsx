import type { Metadata } from "next";
import "./globals.css";
import AuthGuard from "@/components/AuthGuard";
import AppShell from "@/components/AppShell";

export const metadata: Metadata = {
  title: "Madani Social Automation Platform",
  description: "Social content, scheduling and admissions automation for Madani Islamic Academy",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><AuthGuard><AppShell>{children}</AppShell></AuthGuard></body></html>;
}
