import { WorkflowCanvas } from "@/features/workflow/components/WorkflowCanvas"
import { Button } from "@/components/ui/button"
import { Play, RotateCcw } from "lucide-react"

export default function WorkflowPage() {
  return (
    <div className="space-y-6 h-full flex flex-col">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Workflow Monitor</h1>
          <p className="text-muted-foreground mt-1">Real-time visualization of the onboarding lifecycle.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><RotateCcw size={16} className="mr-2" /> Reset View</Button>
          <Button><Play size={16} className="mr-2" /> Resume Workflow</Button>
        </div>
      </div>
      
      <div className="flex-1 w-full min-h-0">
        <WorkflowCanvas />
      </div>
    </div>
  )
}
