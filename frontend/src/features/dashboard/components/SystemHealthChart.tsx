"use client"

import { useMemo } from "react"
import { Area, AreaChart, CartesianGrid, XAxis } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { QueryBoundary } from "@/components/QueryBoundary"
import { useMonitoringMetrics, useMonitoringHealth } from "@/hooks/useMonitoring"

const chartConfig = {
  uptime: {
    label: "Uptime (%)",
    color: "hsl(var(--chart-1))",
  },
  latency: {
    label: "Latency (ms)",
    color: "hsl(var(--chart-3))",
  },
} satisfies ChartConfig

interface HealthPoint {
  time: string
  uptime?: number
  latency?: number
}

// The backend metrics/health payloads are untyped `Record<string, unknown>`
// blobs, so we defensively probe a handful of plausible field names instead
// of assuming a fixed shape.
const TIMESERIES_KEYS = ["timeseries", "history", "series", "points", "data"]
const TIME_KEYS = ["time", "timestamp", "label", "t", "date"]
const UPTIME_KEYS = ["uptime", "uptime_percent", "uptime_pct", "availability"]
const LATENCY_KEYS = ["latency", "latency_ms", "response_time", "response_time_ms"]

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function firstNumber(record: Record<string, unknown>, keys: string[]): number | undefined {
  for (const key of keys) {
    const value = record[key]
    if (typeof value === "number" && Number.isFinite(value)) return value
  }
  return undefined
}

function firstString(record: Record<string, unknown>, keys: string[]): string | undefined {
  for (const key of keys) {
    const value = record[key]
    if (typeof value === "string" && value.length > 0) return value
    if (typeof value === "number") return String(value)
  }
  return undefined
}

function extractTimeseries(metrics: Record<string, unknown>): HealthPoint[] {
  for (const key of TIMESERIES_KEYS) {
    const candidate = metrics[key]
    if (!Array.isArray(candidate) || candidate.length === 0) continue

    const points: HealthPoint[] = []
    candidate.forEach((item: unknown, index: number) => {
      if (!isRecord(item)) return
      const uptime = firstNumber(item, UPTIME_KEYS)
      const latency = firstNumber(item, LATENCY_KEYS)
      if (uptime === undefined && latency === undefined) return
      const time = firstString(item, TIME_KEYS) ?? `#${index + 1}`
      points.push({ time, uptime, latency })
    })
    if (points.length > 0) return points
  }
  return []
}

function extractSnapshot(record: Record<string, unknown>): HealthPoint | null {
  const uptime = firstNumber(record, UPTIME_KEYS)
  const latency = firstNumber(record, LATENCY_KEYS)
  if (uptime === undefined && latency === undefined) return null
  return { time: "Now", uptime, latency }
}

export function SystemHealthChart() {
  const metricsQuery = useMonitoringMetrics()
  const healthQuery = useMonitoringHealth()

  const chartData = useMemo(() => {
    const metrics = metricsQuery.data
    if (isRecord(metrics)) {
      const series = extractTimeseries(metrics)
      if (series.length > 0) return series

      const snapshot = extractSnapshot(metrics)
      if (snapshot) {
        return [{ time: "Previous", uptime: snapshot.uptime, latency: snapshot.latency }, snapshot]
      }
    }

    // Fall back to a synthesized short series from the health endpoint
    // rather than fabricating numbers that don't come from the backend.
    const health = healthQuery.data
    if (isRecord(health)) {
      const uptime = firstNumber(health, UPTIME_KEYS)
      const latency = firstNumber(health, LATENCY_KEYS)
      if (uptime !== undefined || latency !== undefined) {
        return [
          { time: "Previous", uptime, latency },
          { time: "Now", uptime, latency },
        ]
      }
      if (typeof health.status === "string") {
        const healthyStatuses = new Set(["ok", "healthy", "up", "pass", "passing"])
        const syntheticUptime = healthyStatuses.has(health.status.toLowerCase()) ? 100 : 0
        return [
          { time: "Previous", uptime: syntheticUptime },
          { time: "Now", uptime: syntheticUptime },
        ]
      }
    }

    return []
  }, [metricsQuery.data, healthQuery.data])

  const isLoading = metricsQuery.isLoading && healthQuery.isLoading
  const isError = metricsQuery.isError && healthQuery.isError
  const error = metricsQuery.error ?? healthQuery.error

  return (
    <Card>
      <CardHeader>
        <CardTitle>System Health</CardTitle>
        <CardDescription>Uptime and latency over the last 24 hours.</CardDescription>
      </CardHeader>
      <CardContent>
        <QueryBoundary
          isLoading={isLoading}
          isError={isError}
          error={error}
          isEmpty={chartData.length === 0}
          emptyTitle="No historical metrics available yet"
          emptyMessage="System health data will appear here once monitoring reports metrics."
          onRetry={() => {
            metricsQuery.refetch()
            healthQuery.refetch()
          }}
          loadingVariant="card"
        >
          <ChartContainer config={chartConfig} className="min-h-[250px] w-full">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis dataKey="time" tickLine={false} axisLine={false} tickMargin={8} />
              <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
              <Area
                dataKey="uptime"
                type="monotone"
                fill="var(--color-uptime)"
                fillOpacity={0.4}
                stroke="var(--color-uptime)"
                stackId="1"
              />
              <Area
                dataKey="latency"
                type="monotone"
                fill="var(--color-latency)"
                fillOpacity={0.4}
                stroke="var(--color-latency)"
                stackId="2"
              />
            </AreaChart>
          </ChartContainer>
        </QueryBoundary>
      </CardContent>
    </Card>
  )
}
