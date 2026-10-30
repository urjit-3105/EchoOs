import * as React from "react"
import { Handle, Position } from "@xyflow/react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { ChevronDown, ChevronUp, User, Clock } from "lucide-react"

export function WorkflowNode({ data }: any) {
  const [isOpen, setIsOpen] = React.useState(false)

  const statusColors = {
    'completed': 'bg-green-100 text-green-800 border-green-200',
    'in-progress': 'bg-blue-100 text-blue-800 border-blue-200',
    'pending': 'bg-gray-100 text-gray-800 border-gray-200',
    'delayed': 'bg-red-100 text-red-800 border-red-200'
  }

  return (
    <>
      <Handle type="target" position={Position.Top} className="w-3 h-3 bg-primary" />
      <Card className="w-80 shadow-md border-2 hover:border-primary/50 transition-colors bg-card">
        <CardHeader className="p-4 pb-2 border-b">
          <div className="flex justify-between items-start">
            <CardTitle className="text-sm font-bold">{data.label}</CardTitle>
            <Badge variant="outline" className={`capitalize text-[10px] ${statusColors[data.status as keyof typeof statusColors]}`}>
              {data.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="p-4 pt-3 space-y-3">
          <div className="flex justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-1"><User size={12}/> {data.agent}</div>
            <div className="flex items-center gap-1"><Clock size={12}/> {data.duration}</div>
          </div>
          
          <div className="space-y-1">
            <div className="flex justify-between text-[10px] text-muted-foreground">
              <span>Progress</span>
              <span>{data.progress}%</span>
            </div>
            <Progress value={data.progress} className="h-1.5" />
          </div>

          <Collapsible open={isOpen} onOpenChange={setIsOpen}>
            <CollapsibleTrigger className="flex items-center text-xs text-muted-foreground hover:text-foreground transition-colors mt-2">
              {isOpen ? <ChevronUp size={14} className="mr-1" /> : <ChevronDown size={14} className="mr-1" />}
              {isOpen ? "Hide Logs" : "View Logs"}
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-2">
              <div className="bg-muted p-2 rounded-md text-[10px] font-mono h-24 overflow-y-auto space-y-1">
                {data.logs?.map((log: string, i: number) => (
                  <div key={i} className="text-muted-foreground">{'>'} {log}</div>
                ))}
              </div>
            </CollapsibleContent>
          </Collapsible>
        </CardContent>
      </Card>
      <Handle type="source" position={Position.Bottom} className="w-3 h-3 bg-primary" />
    </>
  )
}
