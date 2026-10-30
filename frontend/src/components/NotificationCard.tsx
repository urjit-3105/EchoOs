import * as React from "react"
import { cn } from "@/lib/utils"
import { Bell } from "lucide-react"

interface NotificationCardProps {
  title: string
  description: string
  time: string
  isRead?: boolean
  icon?: React.ReactNode
  className?: string
}

export function NotificationCard({
  title,
  description,
  time,
  isRead = false,
  icon,
  className,
}: NotificationCardProps) {
  return (
    <div
      className={cn(
        "flex gap-4 p-4 rounded-lg border bg-card transition-colors hover:bg-muted/50",
        !isRead && "border-l-4 border-l-primary bg-primary/5",
        className
      )}
    >
      <div className="flex-shrink-0 mt-1 text-primary">
        {icon || <Bell size={18} />}
      </div>
      <div className="flex-1 space-y-1">
        <div className="flex items-start justify-between">
          <p className={cn("text-sm font-medium leading-none", !isRead && "font-semibold")}>
            {title}
          </p>
          <span className="text-xs text-muted-foreground whitespace-nowrap ml-2">
            {time}
          </span>
        </div>
        <p className="text-sm text-muted-foreground line-clamp-2">
          {description}
        </p>
      </div>
    </div>
  )
}
