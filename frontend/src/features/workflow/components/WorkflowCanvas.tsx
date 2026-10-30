"use client"

import * as React from "react"
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  Panel,
  MarkerType
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import { WorkflowNode } from "./nodes/WorkflowNode"
import { Card } from "@/components/ui/card"

const nodeTypes = {
  custom: WorkflowNode,
}

const initialNodes = [
  { id: '1', type: 'custom', position: { x: 250, y: 0 }, data: { label: 'Offer Accepted', status: 'completed', duration: '2 mins', agent: 'System', progress: 100, logs: ['Candidate signed offer via DocuSign', 'Payload received successfully'] } },
  { id: '2', type: 'custom', position: { x: 250, y: 200 }, data: { label: 'Verification', status: 'completed', duration: '4 hrs', agent: 'VerificationAgent', progress: 100, logs: ['Initiated background check', 'Identity verified', 'Clearance granted'] } },
  { id: '3', type: 'custom', position: { x: 250, y: 400 }, data: { label: 'Document Review', status: 'completed', duration: '1 day', agent: 'ComplianceAgent', progress: 100, logs: ['Tax forms validated', 'Direct deposit info stored securely'] } },
  { id: '4', type: 'custom', position: { x: 250, y: 600 }, data: { label: 'Compliance', status: 'completed', duration: '30 mins', agent: 'MonitoringAgent', progress: 100, logs: ['Policy agreements checked', 'Security training enrolled'] } },
  
  // Split into parallel branches
  { id: '5a', type: 'custom', position: { x: 0, y: 800 }, data: { label: 'IT Provisioning', status: 'in-progress', duration: '2 days', agent: 'ExecutionAgent', progress: 60, logs: ['Laptop ordered (MacBook Pro)', 'Software licenses provisioning...', 'Waiting for Okta sync'] } },
  { id: '5b', type: 'custom', position: { x: 500, y: 800 }, data: { label: 'Finance', status: 'completed', duration: '1 day', agent: 'ExecutionAgent', progress: 100, logs: ['Payroll account created', 'Benefits enrollment triggered'] } },
  
  { id: '6', type: 'custom', position: { x: 250, y: 1000 }, data: { label: 'Learning', status: 'pending', duration: '-', agent: 'PlannerAgent', progress: 0, logs: ['Pending prerequisite steps'] } },
  { id: '7', type: 'custom', position: { x: 250, y: 1200 }, data: { label: 'Manager Approval', status: 'pending', duration: '-', agent: 'ManagerAgent', progress: 0, logs: ['Awaiting workflow completion'] } },
  { id: '8', type: 'custom', position: { x: 250, y: 1400 }, data: { label: 'Completed', status: 'pending', duration: '-', agent: 'System', progress: 0, logs: [] } },
]

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e2-3', source: '2', target: '3', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e3-4', source: '3', target: '4', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e4-5a', source: '4', target: '5a', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e4-5b', source: '4', target: '5b', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e5a-6', source: '5a', target: '6', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e5b-6', source: '5b', target: '6', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e6-7', source: '6', target: '7', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e7-8', source: '7', target: '8', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
]

export function WorkflowCanvas() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  return (
    <Card className="h-[800px] w-full relative border-2 overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
      >
        <Background gap={12} size={1} />
        <Controls />
        <MiniMap zoomable pannable nodeColor={(n) => {
          if (n.data?.status === 'completed') return '#22c55e';
          if (n.data?.status === 'in-progress') return '#3b82f6';
          if (n.data?.status === 'delayed') return '#ef4444';
          return '#e5e7eb';
        }} />
        <Panel position="top-left" className="bg-background/80 p-2 rounded-md shadow-sm border text-sm backdrop-blur-sm">
          <strong>Workflow Monitor</strong>
          <p className="text-muted-foreground text-xs mt-1">Onboarding Lifecycle</p>
        </Panel>
      </ReactFlow>
    </Card>
  )
}
