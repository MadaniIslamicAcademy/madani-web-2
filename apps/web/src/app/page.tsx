"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import { apiFetch } from "@/lib/api";
import type { Campaign, Summary } from "@/lib/types";
import StatusBadge from "@/components/StatusBadge";

export default function Dashboard() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  useEffect(() => { Promise.all([apiFetch<Summary>("/dashboard/summary"), apiFetch<Campaign[]>("/campaigns")]).then(([s,c])=>{setSummary(s);setCampaigns(c.slice(0,5));}); }, []);
  const cards = summary ? [
    ["Campaigns", summary.campaigns, "Total workspaces"], ["Needs review", summary.draft_posts, "Draft or generated"], ["Scheduled", summary.scheduled_posts, "Queued for publishing"], ["Published", summary.published_posts, "Successfully completed"], ["Failed", summary.failed_posts, "Needs attention"], ["New leads", summary.new_leads, "Admissions team action"],
  ] : [];
  return <><PageHeader eyebrow="Control centre" title="Assalamualaikum, here is today’s work" description="Review pending content, scheduled posts and new admission leads." action={<Link className="primary-link" href="/campaigns/new">Create campaign</Link>} />
    <section className="metric-grid">{cards.map(([label,value,help])=><article className="metric-card" key={String(label)}><span>{label}</span><strong>{value}</strong><small>{help}</small></article>)}</section>
    <section className="content-grid"><article className="panel"><div className="section-title"><div><span className="eyebrow">Recent work</span><h2>Campaigns</h2></div><Link href="/campaigns">View all</Link></div><div className="table-list">{campaigns.map(c=><Link href={`/campaigns/${c.id}`} className="table-row" key={c.id}><div><strong>{c.name}</strong><small>{c.content_type} · {c.language}</small></div><StatusBadge status={c.status} /></Link>)}{!campaigns.length&&<div className="empty-small">No campaigns yet.</div>}</div></article>
    <article className="panel"><div className="section-title"><div><span className="eyebrow">System</span><h2>Readiness</h2></div></div><div className="readiness"><div><span>Active connections</span><strong>{summary?.active_connections ?? 0}</strong></div><div><span>Approval workflow</span><strong>On</strong></div><div><span>Safe publishing mode</span><strong>Mock ready</strong></div></div><Link className="secondary-link full" href="/connections">Manage connections</Link></article></section>
  </>;
}
