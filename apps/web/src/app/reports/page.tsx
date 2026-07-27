"use client";

import { useEffect, useState } from "react";
import PageHeader from "@/components/PageHeader";
import { apiFetch } from "@/lib/api";
import type { AuditEvent } from "@/lib/types";

export default function ReportsPage(){
 const [events,setEvents]=useState<AuditEvent[]>([]);useEffect(()=>{apiFetch<AuditEvent[]>("/audit?limit=200").then(setEvents)},[]);
 return <><PageHeader eyebrow="Accountability" title="Audit and activity report" description="Every important action remains traceable for administration and troubleshooting."/><section className="panel audit-list">{events.map(event=><article key={event.id}><time>{new Date(event.created_at).toLocaleString()}</time><div><strong>{event.action.replaceAll("."," ")}</strong><small>{event.target_type} · {event.target_id}</small></div><code>{Object.keys(event.metadata_json||{}).length?JSON.stringify(event.metadata_json):"No extra data"}</code></article>)}{!events.length&&<div className="empty-large">No activity recorded yet.</div>}</section></>
}
