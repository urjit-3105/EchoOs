import * as React from "react"
import { cn } from "@/lib/utils"

interface TimelineItemProps {
  title: string
  description?: string
  time: string
  isActive?: boolean
  isLast?: boolean
  icon?: React.ReactNode
  className?: string
}

export function TimelineItem({
  title,
  description,
  time,
  isActive = false,
  isLast = false,
  icon,
  className,
}: TimelineItemProps) {
  return (
    <div className={cn("relative pl-8 pb-8", className)}>
      {!isLast && (
        <div 
          className={cn(
            "absolute left-[11px] top-6 bottom-0 w-[2px]",
            isActive ? "bg-primary" : "bg-border"
          )} 
        />
      )}
      <div 
        className={cn(
          "absolute left-0 top-1 h-6 w-6 rounded-full border-2 flex items-center justify-center bg-background z-10",
          isActive ? "border-primary text-primary" : "border-muted-foreground text-muted-foreground"
        )}
      >
        {icon || <div className={cn("h-2 w-2 rounded-full", isActive ? "bg-primary" : "bg-muted-foreground")} />}
      </div>
      
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-1 sm:gap-4">
        <div>
          <h4 className={cn("text-sm font-semibold", isActive ? "text-foreground" : "text-muted-foreground")}>
            {title}
          </h4>
          {description && (
            <p className="text-sm text-muted-foreground mt-1">{description}</p>
          )}
        </div>
        <time className="text-xs text-muted-foreground whitespace-nowrap sm:mt-0.5">
          {time}
        </time>
      </div>
    </div>
  )
}
