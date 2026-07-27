"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import { apiFetch } from "@/lib/api";
import type { Campaign } from "@/lib/types";

export default function CampaignsPage() {
  const [items,setItems]=useState<Campaign[]>([]);
  useEffect(()=>{apiFetch<Campaign[]>("/campaigns").then(setItems)},[]);
  return <><PageHeader eyebrow="Content operations" title="Campaigns" description="Create one brief, generate platform specific drafts, approve and schedule them." action={<Link className="primary-link" href="/campaigns/new">New campaign</Link>} /><section className="panel"><div className="campaign-list">{items.map(item=><Link href={`/campaigns/${item.id}`} className="campaign-card" key={item.id}><div className="campaign-icon">✦</div><div className="campaign-copy"><div><strong>{item.name}</strong><StatusBadge status={item.status}/></div><p>{item.brief}</p><small>{item.posts.length} platform posts · {new Date(item.created_at).toLocaleDateString()}</small></div></Link>)}{!items.length&&<div className="empty-large"><h3>No campaigns yet</h3><p>Create the first campaign to start the approval workflow.</p></div>}</div></section></>;
}
