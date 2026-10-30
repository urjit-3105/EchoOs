"use client"

import * as React from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { TimelineItem } from "@/components/TimelineItem"
import { motion, AnimatePresence } from "framer-motion"

interface ActivityEvent {
  id: string
  timestamp: string
  agent: string
  action: string
  status: "success" | "pending" | "error"
}

const initialEvents: ActivityEvent[] = [
  { id: '100', timestamp: new Date(Date.now() - 5000).toLocaleTimeString(), agent: 'ExecutionAgent', action: 'Created IT Ticket', status: 'success' },
  { id: '101', timestamp: new Date(Date.now() - 15000).toLocaleTimeString(), agent: 'MonitoringAgent', action: 'Scanned uploaded driver license', status: 'success' },
  { id: '102', timestamp: new Date(Date.now() - 45000).toLocaleTimeString(), agent: 'PlannerAgent', action: 'Dispatched task to Verification', status: 'success' },
  { id: '103', timestamp: new Date(Date.now() - 60000).toLocaleTimeString(), agent: 'ManagerAgent', action: 'Approved budget request', status: 'success' },
]

export function ActivityTimeline() {
  const [events, setEvents] = React.useState<ActivityEvent[]>(initialEvents)
  const containerRef = React.useRef<HTMLDivElement>(null)

  // Simulate incoming real-time events
  React.useEffect(() => {
    const interval = setInterval(() => {
      const newEvent: ActivityEvent = {
        id: Math.random().toString(),
        timestamp: new Date().toLocaleTimeString(),
        agent: ['PlannerAgent', 'VerificationAgent', 'ExecutionAgent', 'MonitoringAgent', 'ManagerAgent'][Math.floor(Math.random() * 5)],
        action: ['Processed document', 'Dispatched API call', 'Verified identity', 'Flagged for review', 'Completed step'][Math.floor(Math.random() * 5)],
        status: Math.random() > 0.8 ? 'error' : Math.random() > 0.5 ? 'pending' : 'success'
      }
      setEvents(prev => [newEvent, ...prev].slice(0, 50)) // Keep last 50
    }, 4000)

    return () => clearInterval(interval)
  }, [])

  return (
    <Card className="h-full flex flex-col overflow-hidden">
      <CardHeader className="border-b bg-muted/20">
        <CardTitle className="flex justify-between items-center">
          <span>Live Activity Feed</span>
          <span className="flex items-center text-xs font-normal text-green-500">
            <span className="relative flex h-2 w-2 mr-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            Live
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto p-6" ref={containerRef}>
        <div className="space-y-4">
          <AnimatePresence initial={false}>
            {events.map((event, index) => (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, height: 0, y: -20 }}
                animate={{ opacity: 1, height: "auto", y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <TimelineItem 
                  title={event.action}
                  description={`Agent: ${event.agent}`}
                  time={event.timestamp}
                  isActive={index === 0}
                  isLast={index === events.length - 1}
                />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </CardContent>
    </Card>
  )
}
