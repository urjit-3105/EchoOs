import * as React from "react"
import { AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

interface ErrorStateProps {
  title?: string
  message: string
  onRetry?: () => void
  className?: string
}

export function ErrorState({ title = "An error occurred", message, onRetry, className }: ErrorStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center p-6 border rounded-lg bg-destructive/10 text-destructive text-center", className)}>
      <AlertCircle className="w-10 h-10 mb-3 opacity-80" />
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="text-sm mt-2 opacity-90 max-w-sm">{message}</p>
      {onRetry && (
        <Button 
          variant="destructive" 
          className="mt-6" 
          onClick={onRetry}
        >
          Try Again
        </Button>
      )}
    </div>
  )
}
