"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DataTable } from "@/components/DataTable"
import { StatusChip, type StatusType } from "@/components/StatusChip"
import { QueryBoundary } from "@/components/QueryBoundary"
import { useEmployees } from "@/hooks/useEmployees"
import { STATUS_LABELS } from "@/constants"
import type { Employee, EmployeeStatus } from "@/types"

const CHIP_STATUS: Record<EmployeeStatus, StatusType> = {
  active: "success",
  accepted: "info",
  invited: "default",
  profile_pending: "warning",
  documents_pending: "warning",
  verifying: "info",
  awaiting_approval: "warning",
  provisioning: "info",
  rejected: "error",
}

export function RecentEmployees() {
  const { data, isLoading, isError, error, refetch } = useEmployees({ limit: 5 })
  const employees = (data ?? [])
    .slice()
    .sort((a, b) => {
      const aTime = a.created_at ? new Date(a.created_at).getTime() : 0
      const bTime = b.created_at ? new Date(b.created_at).getTime() : 0
      return bTime - aTime
    })
    .slice(0, 5)

  const columns = [
    { header: "Name", accessorKey: "full_name" as const },
    { header: "Department", accessorKey: "department" as const },
    { header: "Job Title", accessorKey: "job_title" as const },
    {
      header: "Status",
      cell: (item: Employee) => (
        <StatusChip status={CHIP_STATUS[item.status] ?? "default"} label={STATUS_LABELS[item.status] ?? item.status} />
      ),
    },
  ]

  return (
    <Card className="col-span-1 lg:col-span-2">
      <CardHeader>
        <CardTitle>Recent Employees</CardTitle>
      </CardHeader>
      <CardContent>
        <QueryBoundary
          isLoading={isLoading}
          isError={isError}
          error={error}
          isEmpty={employees.length === 0}
          emptyTitle="No employees yet"
          emptyMessage="Invited employees will appear here once they're added."
          onRetry={() => refetch()}
          loadingVariant="table"
          loadingRows={5}
          loadingColumns={4}
        >
          <DataTable data={employees} columns={columns} emptyMessage="No employees yet." />
        </QueryBoundary>
      </CardContent>
    </Card>
  )
}
