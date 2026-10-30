"use client"

import { StatCard } from "@/components/StatCard"
import { QueryBoundary } from "@/components/QueryBoundary"
import { Users, CheckCircle, Clock, AlertTriangle, ShieldCheck } from "lucide-react"
import { useEmployeeStats } from "@/hooks/useEmployees"
import { useWorkflows } from "@/hooks/useWorkflows"

export function OverviewCards() {
  const statsQuery = useEmployeeStats()
  const failedWorkflowsQuery = useWorkflows({ status: "failed" })

  const isLoading = statsQuery.isLoading || failedWorkflowsQuery.isLoading
  const isError = statsQuery.isError || failedWorkflowsQuery.isError
  const error = statsQuery.error ?? failedWorkflowsQuery.error

  const stats = statsQuery.data
  const delayedCount = failedWorkflowsQuery.data?.length ?? 0

  const averageCompliance =
    typeof stats?.average_compliance_score === "number"
      ? Math.round(stats.average_compliance_score)
      : 0

  return (
    <QueryBoundary
      isLoading={isLoading}
      isError={isError}
      error={error}
      onRetry={() => {
        statsQuery.refetch()
        failedWorkflowsQuery.refetch()
      }}
      loadingVariant="card"
      loadingRows={5}
    >
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <StatCard
          title="Total Employees"
          value={stats?.total_employees ?? 0}
          icon={<Users size={16} className="text-muted-foreground" />}
        />
        <StatCard
          title="Completed Onboarding"
          value={stats?.completed_onboarding ?? stats?.active_employees ?? 0}
          icon={<CheckCircle size={16} className="text-green-500" />}
        />
        <StatCard
          title="Pending Workflows"
          value={stats?.pending_onboarding ?? 0}
          icon={<Clock size={16} className="text-yellow-500" />}
        />
        <StatCard
          title="Delayed Actions"
          value={delayedCount}
          icon={<AlertTriangle size={16} className="text-red-500" />}
        />
        <StatCard
          title="Avg Compliance"
          value={`${averageCompliance}%`}
          icon={<ShieldCheck size={16} className="text-blue-500" />}
        />
      </div>
    </QueryBoundary>
  )
}
