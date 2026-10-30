"use client"

import * as React from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { SearchBar } from "@/components/SearchBar"
import { NotificationCard } from "@/components/NotificationCard"
import { QueryBoundary } from "@/components/QueryBoundary"
import { CheckCircle2, AlertCircle, Info, AlertTriangle, Bell } from "lucide-react"
import { useNotifications, useMarkAllNotificationsRead, useMarkNotificationRead } from "@/hooks/useNotifications"
import { formatDate } from "@/utils/format"

type NotifType = "success" | "warning" | "error" | "info"

export interface NotificationItem {
  id: string
  title: string
  description: string
  time: string
  type: NotifType
  isRead: boolean
}

export function NotificationList() {
  const { data, isLoading, isError, error, refetch } = useNotifications()
  const markAllReadMutation = useMarkAllNotificationsRead()
  const markReadMutation = useMarkNotificationRead()

  const [filter, setFilter] = React.useState<"all" | "unread" | NotifType>("all")
  const [search, setSearch] = React.useState("")

  const rawNotifications = data ?? []

  const formattedNotifications: NotificationItem[] = React.useMemo(() => {
    return rawNotifications.map((n: any) => ({
      id: n.id,
      title: n.title || n.subject || "Notification",
      description: n.message || n.body || n.description || "",
      time: n.created_at ? formatDate(n.created_at) : "Just now",
      type: (n.level || n.type || "info") as NotifType,
      isRead: !!n.read || !!n.is_read,
    }))
  }, [rawNotifications])

  const getIcon = (type: NotifType) => {
    switch (type) {
      case "success": return <CheckCircle2 size={18} className="text-green-500" />
      case "warning": return <AlertTriangle size={18} className="text-yellow-500" />
      case "error": return <AlertCircle size={18} className="text-red-500" />
      default: return <Info size={18} className="text-blue-500" />
    }
  }

  const markAllRead = () => {
    markAllReadMutation.mutate()
  }

  const filtered = formattedNotifications.filter((n) => {
    if (search && !n.title.toLowerCase().includes(search.toLowerCase()) && !n.description.toLowerCase().includes(search.toLowerCase())) return false
    if (filter === "all") return true
    if (filter === "unread") return !n.isRead
    return n.type === filter
  })

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="border-b pb-4">
        <div className="flex justify-between items-center mb-4">
          <CardTitle>Notifications</CardTitle>
          <button onClick={markAllRead} disabled={markAllReadMutation.isPending} className="text-xs text-primary hover:underline disabled:opacity-50">
            Mark all as read
          </button>
        </div>
        <SearchBar placeholder="Search notifications..." onChange={(e) => setSearch(e.target.value)} />
        <div className="flex gap-2 mt-4 flex-wrap">
          {["all", "unread", "success", "warning", "error", "info"].map((f) => (
            <Badge 
              key={f} 
              variant={filter === f ? "default" : "outline"} 
              className="cursor-pointer capitalize"
              onClick={() => setFilter(f as any)}
            >
              {f}
            </Badge>
          ))}
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[400px]">
        <QueryBoundary
          isLoading={isLoading}
          isError={isError}
          error={error}
          isEmpty={filtered.length === 0}
          emptyTitle="No notifications found"
          emptyMessage="Your notification feed will populate as workflow events occur."
          emptyIcon={<Bell className="w-8 h-8 text-zinc-400" />}
          onRetry={() => refetch()}
        >
          <div className="space-y-3">
            {filtered.map((n) => (
              <div key={n.id} onClick={() => !n.isRead && markReadMutation.mutate(n.id)} className="cursor-pointer">
                <NotificationCard 
                  title={n.title}
                  description={n.description}
                  time={n.time}
                  isRead={n.isRead}
                  icon={getIcon(n.type)}
                />
              </div>
            ))}
          </div>
        </QueryBoundary>
      </CardContent>
    </Card>
  )
}
