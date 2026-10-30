"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { QueryBoundary } from "@/components/QueryBoundary"
import { Megaphone } from "lucide-react"
import { useNotifications } from "@/hooks/useNotifications"
import { formatDate } from "@/utils/format"

export function Announcements() {
  const { data, isLoading, isError, error, refetch } = useNotifications()
  const announcements = (data ?? []).filter(
    (notification) => notification.type === "info" || notification.type === "success"
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Megaphone size={18} />
          Announcements
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <QueryBoundary
          isLoading={isLoading}
          isError={isError}
          error={error}
          isEmpty={announcements.length === 0}
          emptyTitle="No announcements"
          emptyMessage="Broadcast notifications will show up here."
          onRetry={() => refetch()}
          loadingVariant="list"
        >
          {announcements.map((announcement) => (
            <div key={announcement.id} className="flex justify-between items-start border-b last:border-0 pb-3 last:pb-0">
              <div>
                <p className="font-medium text-sm">{announcement.title}</p>
                <p className="text-xs text-muted-foreground mt-1">{formatDate(announcement.created_at)}</p>
              </div>
              <Badge variant="secondary" className="text-[10px]">{announcement.type}</Badge>
            </div>
          ))}
        </QueryBoundary>
      </CardContent>
    </Card>
  )
}
