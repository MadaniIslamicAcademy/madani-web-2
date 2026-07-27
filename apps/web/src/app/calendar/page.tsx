"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import { apiFetch } from "@/lib/api";
import type { Campaign, SocialPost } from "@/lib/types";

export default function CalendarPage(){const [posts,setPosts]=useState<(SocialPost&{campaignName:string})[]>([]);useEffect(()=>{apiFetch<Campaign[]>("/campaigns").then(items=>setPosts(items.flatMap(c=>c.posts.filter(p=>p.scheduled_for).map(p=>({...p,campaignName:c.name}))).sort((a,b)=>String(a.scheduled_for).localeCompare(String(b.scheduled_for)))) )},[]);return <><PageHeader eyebrow="Publishing plan" title="Content calendar" description="Only approved posts can enter the publishing schedule."/><section className="panel timeline">{posts.map(post=><Link href={`/campaigns/${post.campaign_id}`} className="timeline-item" key={post.id}><time>{post.scheduled_for?new Date(post.scheduled_for).toLocaleString():""}</time><div><strong>{post.campaignName}</strong><small>{post.platform}</small></div><StatusBadge status={post.status}/></Link>)}{!posts.length&&<div className="empty-large"><h3>No scheduled posts</h3><p>Approve a post and choose a future date from its campaign screen.</p></div>}</section></>}
