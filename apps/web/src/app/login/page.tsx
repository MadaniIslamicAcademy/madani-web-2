"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, setCsrfToken } from "@/lib/api";
import type { User } from "@/lib/types";

interface AuthResponse { user: User; csrf_token: string; }

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@madaniislamicacademy.com");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(""); setLoading(true);
    try {
      const result = await apiFetch<AuthResponse>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      setCsrfToken(result.csrf_token);
      router.replace("/");
    } catch (e) { setError(e instanceof Error ? e.message : "Login failed"); }
    finally { setLoading(false); }
  }

  return <main className="login-page">
    <section className="login-visual"><div className="login-logo">M</div><span className="eyebrow light">Madani Islamic Academy Ltd</span><h1>Plan, approve and publish with control.</h1><p>One secure workspace for social campaigns, scheduled publishing and WhatsApp admission leads.</p><ul><li>AI drafts stay under academy rules</li><li>Nothing publishes before approval</li><li>Every action has a history</li></ul></section>
    <section className="login-card"><div><span className="eyebrow">Secure administrator access</span><h2>Welcome back</h2><p>Use the bootstrap administrator details from your private environment file.</p></div><form onSubmit={submit}><label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required /></label><label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} required minLength={8} /></label>{error && <div className="error-box">{error}</div>}<button className="primary-button" disabled={loading}>{loading ? "Signing in" : "Sign in"}</button></form></section>
  </main>;
}
