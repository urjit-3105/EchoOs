"use client"

import { useMemo } from "react"
import { Bar, BarChart, CartesianGrid, XAxis } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { QueryBoundary } from "@/components/QueryBoundary"
import { useEmployees } from "@/hooks/useEmployees"

const chartConfig = {
  onboarded: {
    label: "Employees Onboarded",
    color: "hsl(var(--primary))",
  },
} satisfies ChartConfig

const WEEKS_TO_SHOW = 6
const MS_PER_WEEK = 7 * 24 * 60 * 60 * 1000

function startOfWeek(date: Date): Date {
  const d = new Date(date)
  d.setHours(0, 0, 0, 0)
  const day = d.getDay() // 0 = Sunday
  d.setDate(d.getDate() - day)
  return d
}

function shortDateLabel(date: Date): string {
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" })
}

export function WeeklyOnboardingChart() {
  const { data, isLoading, isError, error, refetch } = useEmployees()
  const employees = Array.isArray(data) ? data : (data as any)?.items ?? []

  const chartData = useMemo(() => {
    const now = new Date()
    const currentWeekStart = startOfWeek(now)
    const weekStarts: Date[] = []
    for (let i = WEEKS_TO_SHOW - 1; i >= 0; i--) {
      weekStarts.push(new Date(currentWeekStart.getTime() - i * MS_PER_WEEK))
    }

    return weekStarts.map((weekStart, idx) => {
      const weekEnd = new Date(weekStart.getTime() + MS_PER_WEEK)
      const isLastBucket = idx === weekStarts.length - 1
      const count = (Array.isArray(employees) ? employees : []).reduce((total: number, employee: any) => {
        if (!employee.created_at) return total
        const created = new Date(employee.created_at)
        if (Number.isNaN(created.getTime())) return total
        const inRange = isLastBucket
          ? created >= weekStart && created <= now
          : created >= weekStart && created < weekEnd
        return inRange ? total + 1 : total
      }, 0)
      return { week: `Week of ${shortDateLabel(weekStart)}`, onboarded: count }
    })
  }, [employees])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Weekly Onboarding</CardTitle>
        <CardDescription>Number of employees onboarded per week.</CardDescription>
      </CardHeader>
      <CardContent>
        <QueryBoundary
          isLoading={isLoading}
          isError={isError}
          error={error}
          isEmpty={employees.length === 0}
          emptyTitle="No onboarding data yet"
          emptyMessage="Weekly onboarding counts will appear here once employees join."
          onRetry={() => refetch()}
          loadingVariant="card"
        >
          <ChartContainer config={chartConfig} className="min-h-[250px] w-full">
            <BarChart accessibilityLayer data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis
                dataKey="week"
                tickLine={false}
                tickMargin={10}
                axisLine={false}
              />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar dataKey="onboarded" fill="var(--color-onboarded)" radius={4} />
            </BarChart>
          </ChartContainer>
        </QueryBoundary>
      </CardContent>
    </Card>
  )
}
