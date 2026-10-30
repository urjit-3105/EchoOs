import * as React from "react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

export type StatusType = "success" | "warning" | "error" | "info" | "default"

interface StatusChipProps extends React.HTMLAttributes<HTMLDivElement> {
  status: StatusType
  label: string
}

export function StatusChip({ status, label, className, ...props }: StatusChipProps) {
  const variants: Record<StatusType, string> = {
    success: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 border-green-200 dark:border-green-800",
    warning: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400 border-yellow-200 dark:border-yellow-800",
    error: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 border-red-200 dark:border-red-800",
    info: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 border-blue-200 dark:border-blue-800",
    default: "bg-muted text-muted-foreground border-border",
  }

  return (
    <Badge 
      variant="outline" 
      className={cn("px-2.5 py-0.5 text-xs font-medium border", variants[status], className)}
      {...props}
    >
      {label}
    </Badge>
  )
}
