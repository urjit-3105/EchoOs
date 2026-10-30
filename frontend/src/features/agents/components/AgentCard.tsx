import * as React from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Activity, Bot, Cpu, Zap, ServerCrash } from "lucide-react"
import { cn } from "@/lib/utils"

interface AgentProps {
  name: string
  role: string
  status: "Online" | "Degraded" | "Offline"
  health: number
  tasksCompleted: number
  avgTime: string
  currentTask?: string
  queueLength: number
}

export function AgentCard({ agent }: { agent: AgentProps }) {
  const isHealthy = agent.health > 80
  const isDegraded = agent.status === "Degraded"
  const isOffline = agent.status === "Offline"

  const StatusIcon = isOffline ? ServerCrash : isDegraded ? Activity : Zap

  return (
    <Card className="hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1">
      <CardHeader className="flex flex-row justify-between items-start pb-2">
        <div className="flex gap-3 items-center">
          <div className={cn(
            "p-3 rounded-full flex items-center justify-center",
            isOffline ? "bg-red-100 text-red-600" : isDegraded ? "bg-yellow-100 text-yellow-600" : "bg-primary/10 text-primary"
          )}>
            <Bot size={20} />
          </div>
          <div>
            <CardTitle className="text-lg">{agent.name}</CardTitle>
            <p className="text-xs text-muted-foreground">{agent.role}</p>
          </div>
        </div>
        <Badge variant={isOffline ? "destructive" : isDegraded ? "outline" : "default"} className={cn(isDegraded && "text-yellow-600 border-yellow-200 bg-yellow-50")}>
          <StatusIcon size={12} className="mr-1" />
          {agent.status}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-4 pt-4 border-t mt-2">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground text-xs">Tasks Completed</p>
            <p className="font-semibold text-lg">{agent.tasksCompleted.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Avg. Execution</p>
            <p className="font-semibold text-lg">{agent.avgTime}</p>
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground flex items-center gap-1"><Cpu size={12} /> System Health</span>
            <span className={isHealthy ? "text-green-600" : "text-yellow-600"}>{agent.health}%</span>
          </div>
          <Progress value={agent.health} className={cn("h-1.5", isHealthy ? "" : "[&>div]:bg-yellow-500")} />
        </div>

        <div className="bg-muted rounded-md p-3 space-y-2">
          <div className="flex justify-between text-xs">
            <span className="font-medium">Current Task</span>
            <Badge variant="secondary" className="text-[9px] px-1 py-0 rounded-sm">Queue: {agent.queueLength}</Badge>
          </div>
          <p className="text-xs text-muted-foreground line-clamp-1 truncate" title={agent.currentTask || "Idle"}>
            {agent.currentTask || "Idle"}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
