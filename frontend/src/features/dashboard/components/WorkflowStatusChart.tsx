"use client"

import { useMemo } from "react"
import { Bar, BarChart, CartesianGrid, XAxis, Cell } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { QueryBoundary } from "@/components/QueryBoundary"
import { useWorkflows } from "@/hooks/useWorkflows"
import type { WorkflowStatus } from "@/types"

const chartConfig = {
  value: {
    label: "Workflows",
    color: "hsl(var(--primary))",
  },
  Success: {
    label: "Success",
    color: "hsl(var(--chart-2))", // Greenish
  },
  Pending: {
    label: "Pending",
    color: "hsl(var(--chart-4))", // Yellowish
  },
  Delayed: {
    label: "Delayed",
    color: "hsl(var(--destructive))", // Red
  },
} satisfies ChartConfig

const BUCKET_FOR_STATUS: Record<WorkflowStatus, "Success" | "Pending" | "Delayed"> = {
  completed: "Success",
  running: "Pending",
  pending: "Pending",
  paused: "Pending",
  failed: "Delayed",
  cancelled: "Delayed",
}

export function WorkflowStatusChart() {
  const { data, isLoading, isError, error, refetch } = useWorkflows()
  const workflows = data ?? []

  const chartData = useMemo(() => {
    const buckets: Record<"Success" | "Pending" | "Delayed", number> = {
      Success: 0,
      Pending: 0,
      Delayed: 0,
    }
    for (const workflow of workflows) {
      const bucket = BUCKET_FOR_STATUS[workflow.status] ?? "Pending"
      buckets[bucket] += 1
    }
    return [
      { name: "Success", value: buckets.Success },
      { name: "Pending", value: buckets.Pending },
      { name: "Delayed", value: buckets.Delayed },
    ]
  }, [workflows])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Workflow Status</CardTitle>
        <CardDescription>Current status of all active and completed workflows.</CardDescription>
      </CardHeader>
      <CardContent>
        <QueryBoundary
          isLoading={isLoading}
          isError={isError}
          error={error}
          isEmpty={workflows.length === 0}
          emptyTitle="No workflows yet"
          emptyMessage="Workflow status will appear here once onboarding begins."
          onRetry={() => refetch()}
          loadingVariant="card"
        >
          <ChartContainer config={chartConfig} className="min-h-[250px] w-full">
            <BarChart accessibilityLayer data={chartData} layout="vertical" margin={{ top: 0, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid horizontal={false} strokeDasharray="3 3" />
              <XAxis type="number" hide />
              <XAxis dataKey="name" type="category" axisLine={false} tickLine={false} />
              <ChartTooltip content={<ChartTooltipContent hideLabel />} />
              <Bar dataKey="value" radius={4}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={chartConfig[entry.name as keyof typeof chartConfig]?.color || 'var(--color-primary)'} />
                ))}
              </Bar>
            </BarChart>
          </ChartContainer>
        </QueryBoundary>
      </CardContent>
    </Card>
  )
}
