"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TimelineItem } from "@/components/TimelineItem"
import { QueryBoundary } from "@/components/QueryBoundary"
import { FileEdit, UserPlus, CheckCircle, Activity } from "lucide-react"
import { useAudit } from "@/hooks/useAudit"
import { formatRelativeTime } from "@/utils/format"
import type { AuditEntry } from "@/types"

function iconForAction(action: string) {
  const normalized = action.toLowerCase()
  if (normalized.includes("create") || normalized.includes("invite")) {
    return <UserPlus size={14} />
  }
  if (normalized.includes("complete") || normalized.includes("approve")) {
    return <CheckCircle size={14} />
  }
  if (normalized.includes("update") || normalized.includes("edit")) {
    return <FileEdit size={14} />
  }
  return <Activity size={14} />
}

function titleFor(entry: AuditEntry) {
  const resource = entry.resource_type
    ? entry.resource_type.charAt(0).toUpperCase() + entry.resource_type.slice(1)
    : "Resource"
  const action = entry.action ? entry.action.charAt(0).toUpperCase() + entry.action.slice(1) : "Updated"
  return `${resource} ${action}`
}

function descriptionFor(entry: AuditEntry) {
  const parts: string[] = []
  if (entry.actor) parts.push(`by ${entry.actor}`)
  if (entry.resource_id) parts.push(`(${entry.resource_id})`)
  return parts.length ? parts.join(" ") : undefined
}

export function RecentActivity() {
  const { data, isLoading, isError, error, refetch } = useAudit({ limit: 10 })
  const entries = data ?? []

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <QueryBoundary
          isLoading={isLoading}
          isError={isError}
          error={error}
          isEmpty={entries.length === 0}
          emptyTitle="No activity yet"
          emptyMessage="Audit events will show up here as they happen."
          onRetry={() => refetch()}
          loadingVariant="list"
        >
          {entries.map((entry, index) => (
            <TimelineItem
              key={entry.id}
              title={titleFor(entry)}
              description={descriptionFor(entry)}
              time={formatRelativeTime(entry.created_at)}
              isActive={index === 0}
              isLast={index === entries.length - 1}
              icon={iconForAction(entry.action)}
            />
          ))}
        </QueryBoundary>
      </CardContent>
    </Card>
  )
}
