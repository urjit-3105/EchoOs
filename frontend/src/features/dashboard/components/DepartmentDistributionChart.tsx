"use client"

import { useMemo } from "react"
import { Cell, Pie, PieChart } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent } from "@/components/ui/chart"
import { QueryBoundary } from "@/components/QueryBoundary"
import { useEmployeeStats, useEmployees } from "@/hooks/useEmployees"

const COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
]

const chartConfig = {
  value: {
    label: "Employees",
  },
} satisfies ChartConfig

export function DepartmentDistributionChart() {
  const statsQuery = useEmployeeStats()
  const employeesQuery = useEmployees()

  const byDepartment = statsQuery.data?.by_department
  const hasStatsBreakdown = !!byDepartment && Object.keys(byDepartment).length > 0

  const isLoading = hasStatsBreakdown ? statsQuery.isLoading : statsQuery.isLoading || employeesQuery.isLoading
  const isError = statsQuery.isError || (!hasStatsBreakdown && employeesQuery.isError)
  const error = statsQuery.error ?? employeesQuery.error

  const chartData = useMemo(() => {
    if (byDepartment && Object.keys(byDepartment).length > 0) {
      return Object.entries(byDepartment).map(([name, value]) => ({ name, value }))
    }
    const employees = employeesQuery.data ?? []
    const counts = new Map<string, number>()
    for (const employee of employees) {
      const department = employee.department?.trim() || "Unassigned"
      counts.set(department, (counts.get(department) ?? 0) + 1)
    }
    return Array.from(counts.entries()).map(([name, value]) => ({ name, value }))
  }, [byDepartment, employeesQuery.data])

  return (
    <Card className="flex flex-col">
      <CardHeader className="items-center pb-0">
        <CardTitle>Department Distribution</CardTitle>
        <CardDescription>Employee count by department</CardDescription>
      </CardHeader>
      <CardContent className="flex-1 pb-0">
        <QueryBoundary
          isLoading={isLoading}
          isError={isError}
          error={error}
          isEmpty={chartData.length === 0}
          emptyTitle="No department data yet"
          emptyMessage="Department distribution will appear here once employees are added."
          onRetry={() => {
            statsQuery.refetch()
            employeesQuery.refetch()
          }}
          loadingVariant="card"
        >
          <ChartContainer config={chartConfig} className="mx-auto aspect-square max-h-[300px]">
            <PieChart>
              <ChartTooltip content={<ChartTooltipContent hideLabel />} />
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={2}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <ChartLegend content={<ChartLegendContent />} className="-translate-y-2 flex-wrap gap-2" />
            </PieChart>
          </ChartContainer>
        </QueryBoundary>
      </CardContent>
    </Card>
  )
}
